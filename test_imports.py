try:
    from database.models.orm_jk import orm_get_all_jks, orm_get_jk_by_id
    print("orm_jk - OK")
except Exception as e:
    print(f"orm_jk - ERROR: {e}")

try:
    from database.models.orm_user import orm_get_user_by_id
    print("orm_user - OK")
except Exception as e:
    print(f"orm_user - ERROR: {e}")

try:
    from database.models.orm_user_jk import orm_get_jks_by_user_admin
    print("orm_user_jk - OK")
except Exception as e:
    print(f"orm_user_jk - ERROR: {e}")

try:
    from database.models.orm_jk_service_provider import (
        orm_add_service_provider,
        orm_get_service_providers_by_jk,
        orm_get_service_provider_by_category,
        orm_update_service_provider,
        orm_deactivate_service_provider
    )
    print("orm_jk_service_provider - OK")
except Exception as e:
    print(f"orm_jk_service_provider - ERROR: {e}")

try:
    from database.enums.user_enums import UserRole
    print("user_enums - OK")
except Exception as e:
    print(f"user_enums - ERROR: {e}")

try:
    from database.enums.offer_enums import OfferCategory
    print("offer_category_enum - OK")
except Exception as e:
    print(f"offer_category_enum - ERROR: {e}")

try:
    from keyboards.reply import MAIN_KB, get_keyboard
    print("reply keyboards - OK")
except Exception as e:
    print(f"reply keyboards - ERROR: {e}")

try:
    from keyboards.service_provider_keyboards import (
        get_category_keyboard,
        get_providers_keyboard,
        get_jk_selection_keyboard,
        get_phone_input_keyboard,
        get_confirmation_keyboard
    )
    print("service_provider_keyboards - OK")
except Exception as e:
    print(f"service_provider_keyboards - ERROR: {e}")

try:
    from services.service_provider_service import (
        check_service_management_access,
        validate_responsible_user,
        validate_organization_name,
        validate_work_schedule
    )
    print("service_provider_service - OK")
except Exception as e:
    print(f"service_provider_service - ERROR: {e}")

try:
    from utils.phone_validator import validate_phone, PhoneValidator
    print("phone_validator - OK")
except Exception as e:
    print(f"phone_validator - ERROR: {e}")
