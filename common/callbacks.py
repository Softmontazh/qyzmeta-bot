# coding: utf-8


"""Строки для действий с лотами в системе."""


class LotActions:
    # Базовые действия
    FEEDBACK = "feedback_lot_"  # Отзывы
    WRITE_TO_OWNER = "write_to_owner_lot_"  # Написать владельцу
    REPORT = "report_lot_"  # Пожаловаться на лот
    RESUBMIT = "resubmit_lot_"  # Подать снова

    # Для пользователей
    EDIT = "edit_lot_"  # Редактировать лот
    DELETE = "delete_lot_"  # Удалить лот
    ARCHIVE = "archive_lot_"  # В архив
    ACTIVATE = "activate_lot_"  # Активировать
    RENEW = "renew_lot_"  # Продлить

    # Для админов
    APPROVE = "approve_lot_"  # Одобрить
    REJECT = "reject_lot_"  # Отклонить
    BLOCKING = "blocking_lot_"  # Заблокировать
    UNBLOCKING = "unblocking_lot_"  # Разблокировать


class JKActions:
    # Базовые действия
    INFO = "info_jk_"  # Информация о ЖК
    CANCEL_REGISTRATION = "cancel_registration_jk_"  # Отменить регистрацию в ЖК
    MANAGE = "manage_jk_"  # Управление ЖК


class OfferActions:
    # Базовые действия
    INFO = "info_offer_"  # Информация о заявке
    CANCEL_OFFER = "cancel_offer_"  # Отменить заявку
    ARCHIVE_OFFER = "archive_offer_"  # Архивировать заявку
