try:
    import handlers.fsm.manage_service_providers_fsm as m
    print("Импорт успешен")
    print(f"Роутер найден: {hasattr(m, 'manage_service_providers_router')}")
    if hasattr(m, 'manage_service_providers_router'):
        print(f"Тип роутера: {type(m.manage_service_providers_router)}")
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
