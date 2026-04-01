CERTIFICATE_CODE = 'certificate_code'
PLATFORM_NAME = 'gladius_art'


class TYPE_IMAGE:
    VIEW = 'view'
    QR_CODE = 'qr_code'
    TERM_CONDITION = 'term_and_condition'


class STATUS_REQUEST:
    REQUEST_RECEIVED = 1
    REQUEST_APPROVED = 2
    REQUEST_DENIED = 3
    REQUEST_CANCELED = 4


CATEGORY_CHOICES = (
    ('painting', 'Painting'),
    ('sculpture', 'Sculpture'),
)

STATUS_CHOICES = (
    ('', '----'),
    ('available', 'Available for sale'),
    ('sold', 'Sold'),
    ('not_for_sale', 'Not for sale'),
    ('lost', 'Lost'),
    ('consignment', 'Consignment'),
    ('donated_gifted', 'Donated/Gifted'),
    ('under_maintenance', 'Under Maintenance'),
    ('in_stock', 'In Stock'),
)

PROCESSING_STATUS_CHOICES = (
    ('', '----'),
    ('information_received', 'Information received'),
    ('certificate_exported', 'Certificate exported'),
    ('shipping_unit_received', 'Shipping unit received'),
    ('completed', 'Completed'),
)

STATUS_REQUEST_CHOICES = (
    (STATUS_REQUEST.REQUEST_RECEIVED, 'Request received'),
    (STATUS_REQUEST.REQUEST_APPROVED, 'Request approved'),
    (STATUS_REQUEST.REQUEST_DENIED, 'Request denied'),
    (STATUS_REQUEST.REQUEST_CANCELED, 'Request canceled'),
)

EXPORT = 'export'
VERIFY = 'verify'
ACTION_CHOICES = [
    (EXPORT, 'Export Certificate'),
    (VERIFY, 'Verify Certificate'),
]

EXHIBITION_TYPE_CHOICES = [
    ('free_ticket', 'Free Ticket'),
    ('ticket_sale', 'Ticket Sale'),
    ('private_event', 'Private Event'),
]
