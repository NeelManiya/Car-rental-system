from fastapi import APIRouter, HTTPException, status
from database.database import SessionLocal
from src.models.user import User, OTP
from src.schemas.user import (
    RegisterUserSchema,
    GetAllUserSchema,
    UpdateUserSchema,
    ForgetPasswordSchema,
    ResetPasswordSchema,
)
import uuid, random
from src.utils.user import (
    pwd_context,
    find_same_email,
    send_email,
    pass_checker,
    get_token,
    decode_token,
    gen_otp,
)
from logs.log_config import logger  # Assuming logger is configured

user_router = APIRouter()
db = SessionLocal()


# -------------------- ~ REGISTER USER ~ --------------------#


@user_router.post("/register_user")
def register_user(user: RegisterUserSchema):
    logger.info(f"Registering new user: {user.email}")
    new_user = User(
        id=str(uuid.uuid4()),
        name=user.name,
        email=user.email,
        phone_no=user.phone_no,
        password=pwd_context.hash(user.password),
    )

    find_minimum_one_entry = db.query(User).first()
    if find_minimum_one_entry:
        logger.warning(f"Email already exists: {user.email}")
        find_same_email(user.email)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User registered successfully: {user.email}")
    return "User registered successfully, now proceed for verification"


# -------------------- ~ GENERATE OTP ~ --------------------#


@user_router.post("/generate otp")
def generate_otp(email: str):
    logger.info(f"Generating OTP for email: {email}")
    gen_otp(email)
    logger.info(f"OTP generated and sent to email: {email}")
    return "OTP generated successfully, now check your email"


# -------------------- ~ VERIFICATION USING OTP ~ --------------------#


@user_router.get("/verify_otp")
def verify_otp(email: str, otp: str):
    logger.info(f"Verifying OTP for email: {email}")
    find_user_with_email = (
        db.query(User)
        .filter(
            User.email == email,
            User.is_active == True,
            User.is_verified == False,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user_with_email:
        logger.error(f"User not found: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    find_otp = db.query(OTP).filter(OTP.email == email, OTP.otp == otp).first()

    if not find_otp:
        logger.error(f"OTP not found for email: {email}")
        raise HTTPException(status_code=400, detail="OTP not found")

    find_user_with_email.is_verified = True
    db.delete(find_otp)
    db.commit()
    db.refresh(find_user_with_email)
    logger.info(f"OTP verified successfully for email: {email}")
    return "OTP verified successfully"


# -------------------- ~ LOGIN USER ~ --------------------#


@user_router.get("/login_user")
def login_user(email: str, password: str):
    logger.info(f"User login attempt: {email}")
    find_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.is_active == True,
            User.is_verified == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user:
        logger.error(f"User not found for login: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    pass_checker(password, find_user.password)

    access_token = get_token(
        find_user.id, find_user.name, find_user.email, find_user.phone_no
    )

    logger.info(f"Login successful for user: {email}")
    return access_token, "Login successfully"


# -------------------- ~ GET SINGLE USER ~ --------------------#


@user_router.get("/get_user/{user_email}", response_model=GetAllUserSchema)
def get_user(user_email: str):
    logger.info(f"Fetching user details for: {user_email}")
    find_user = (
        db.query(User)
        .filter(
            User.email == user_email,
            User.is_active == True,
            User.is_verified == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user:
        logger.error(f"User not found: {user_email}")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User details retrieved successfully for: {user_email}")
    return find_user


# -------------------- ~ GET ALL USERS ~ --------------------#


@user_router.get("/get_all_user", response_model=list[GetAllUserSchema])
def get_all_user():
    logger.info("Fetching all active, verified users")
    find_all_user = (
        db.query(User)
        .filter(
            User.is_active == True, User.is_verified == True, User.is_deleted == False
        )
        .all()
    )

    if not find_all_user:
        logger.error("No active users found")
        raise HTTPException(status_code=404, detail="No active users found")

    logger.info(f"Found {len(find_all_user)} active users")
    return find_all_user


# -------------------- ~ UPDATE USER ~ --------------------#


@user_router.patch("/update_user")
def update_user(password: str, token: str, user: UpdateUserSchema):
    logger.info(f"Updating user details for email: {user.email}")
    user_details = decode_token(token)
    user_id, name, email, phone_no = user_details

    find_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.password == password,
            User.is_active == True,
            User.is_verified == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user:
        logger.error(f"User not found for update: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    new_userschema_without_none = user.model_dump(exclude_none=True)

    for key, value in new_userschema_without_none.items():
        if key == "password":
            setattr(find_user, key, pwd_context.hash(value))
        else:
            find_same_email(value)
            setattr(find_user, key, value)

    db.commit()
    db.refresh(find_user)
    logger.info(f"User details updated successfully for email: {email}")
    return {"message": "User updated successfully", "data": find_user}


# -------------------- ~ DELETE USER ~ --------------------#


@user_router.delete("/delete_user")
def delete_user(token: str):
    logger.info("Deleting user")
    user_details = decode_token(token)
    user_id, name, email, phone_no = user_details

    find_user = (
        db.query(User)
        .filter(User.email == email, User.is_active == True, User.is_verified == True)
        .first()
    )

    if not find_user:
        logger.error(f"User not found for deletion: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    if find_user.is_deleted == True:
        logger.warning(f"User already deleted: {email}")
        raise HTTPException(status_code=400, detail="User account already deleted")

    find_user.is_deleted = True
    find_user.is_active = False
    find_user.is_verified = False
    db.commit()
    db.refresh(find_user)
    logger.info(f"User deleted successfully: {email}")
    return {"message": "User deleted successfully", "data": find_user}


# -------------------- ~ OTP FOR FORGOT PASSWORD ~ --------------------#


@user_router.post("/generate_otp_for_forget_password")
def generate_otp_for_forget_password(email: str):
    logger.info(f"Generating OTP for password reset for email: {email}")
    gen_otp(email)
    logger.info(f"OTP generated for email: {email}")
    return "OTP sent successfully"


# -------------------- ~ FORGOT PASSWORD ~ --------------------#


@user_router.patch("/forget_password")
def forget_password(email: str, otp: str, user: ForgetPasswordSchema):
    logger.info(f"Processing password reset for email: {email}")
    find_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.is_active == True,
            User.is_verified == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user:
        logger.error(f"User not found for password reset: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    find_otp = db.query(OTP).filter(OTP.email == email, OTP.otp == otp).first()

    if not find_otp:
        logger.error(f"OTP not found for password reset: {email}")
        raise HTTPException(status_code=400, detail="OTP not found")

    if user.new_password == user.confirm_password:
        setattr(find_user, "password", pwd_context.hash(user.confirm_password))
    else:
        logger.error("Password confirmation does not match new password")
        raise HTTPException(
            status_code=400, detail="Password confirmation does not match new password"
        )

    db.delete(find_otp)
    db.commit()
    db.refresh(find_user)

    logger.info(f"Password changed successfully for email: {email}")
    return "Password changed successfully"


# -------------------- ~ RESET PASSWORD ~ --------------------#


@user_router.patch("/reset_password")
def reset_password(token: str, user: ResetPasswordSchema):
    logger.info(f"Resetting password for user: {user.email}")
    user_details = decode_token(token)
    user_id, name, email, phone_no = user_details

    find_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.is_active == True,
            User.is_verified == True,
            User.is_deleted == False,
        )
        .first()
    )

    if not find_user:
        logger.error(f"User not found for password reset: {email}")
        raise HTTPException(status_code=404, detail="User not found")

    pass_checker(user.old_password, find_user.password)

    if user.new_password == user.confirm_password:
        setattr(find_user, "password", pwd_context.hash(user.confirm_password))
    else:
        logger.error("Password confirmation does not match new password")
        raise HTTPException(
            status_code=400, detail="Password confirmation does not match new password"
        )

    db.commit()
    db.refresh(find_user)

    logger.info(f"Password reset successfully for user: {email}")
    return "Password reset successfully"
