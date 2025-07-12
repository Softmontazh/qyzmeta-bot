import sys
print("Starting import test...")

try:
    print("1. Testing aiogram imports...")
    from aiogram import F, Router
    from aiogram.filters import Command
    from aiogram.fsm.state import StatesGroup, State
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    print("   aiogram - OK")
    
    print("2. Testing sqlalchemy...")
    from sqlalchemy.ext.asyncio import AsyncSession
    print("   sqlalchemy - OK")
    
    print("3. Testing database.models.orm_jk...")
    from database.models.orm_jk import orm_get_all_jks, orm_get_jk_by_id
    print("   orm_jk - OK")
    
    print("4. Testing database.models.orm_user...")
    from database.models.orm_user import orm_get_user_by_id
    print("   orm_user - OK")
    
    print("5. Testing database.models.orm_user_jk...")
    from database.models.orm_user_jk import orm_get_jks_by_user_admin
    print("   orm_user_jk - OK")
    
    print("6. Testing database.models.orm_jk_service_provider...")
    from database.models.orm_jk_service_provider import (
        orm_add_service_provider,
        orm_get_service_providers_by_jk,
        orm_get_service_provider_by_category,
        orm_update_service_provider,
        orm_deactivate_service_provider
    )
    print("   orm_jk_service_provider - OK")
    
    print("7. Testing database.enums.user_enums...")
    from database.enums.user_enums import UserRole
    print("   user_enums - OK")
    
    print("8. Testing database.enums.offer_category_enum...")
    from database.enums.offer_category_enum import OfferCategory
    print("   offer_category_enum - OK")
    
    print("9. Testing keyboards.reply...")
    from keyboards.reply import MAIN_KB, get_keyboard
    print("   reply keyboards - OK")
    
    print("10. Testing keyboards.service_provider_keyboards...")
    from keyboards.service_provider_keyboards import (
        get_category_keyboard,
        get_providers_keyboard,
        get_jk_selection_keyboard,
        get_phone_input_keyboard,
        get_confirmation_keyboard
    )
    print("   service_provider_keyboards - OK")
    
    print("11. Testing services.service_provider_service...")
    from services.service_provider_service import (
        check_service_management_access,
        validate_responsible_user,
        validate_organization_name,
        validate_work_schedule
    )
    print("   service_provider_service - OK")
    
    print("12. Testing utils.phone_validator...")
    from utils.phone_validator import validate_phone, PhoneValidator
    print("   phone_validator - OK")
    
    print("13. Creating router...")
    manage_service_providers_router = Router()
    print("   Router created successfully!")
    
    print("ALL IMPORTS SUCCESSFUL!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
