"""Seed data for OOH media types (adbuq-style picker + market standards)."""

# (name, slug, category, is_digital, is_selectable, sort_order, parent_slug)
# parent_slug=None for top-level groups or standalone types

MEDIA_TYPE_SEED = [
    # Group headers (not selectable on create)
    ('All Digital', 'all-digital', 'digital', True, False, 0, None),
    ('All Static', 'all-static', 'static', False, False, 100, None),

    # Digital (from adbuq + market)
    ('Digital Billboard', 'digital-billboard', 'digital', True, True, 10, 'all-digital'),
    ('Digital Pole Signs', 'digital-pole-signs', 'digital', True, True, 11, 'all-digital'),
    ('Digital Pylon', 'digital-pylon', 'digital', True, True, 12, 'all-digital'),
    ('Digital SMD', 'digital-smd', 'digital', True, True, 13, 'all-digital'),
    ('LED Video Wall', 'led-video-wall', 'digital', True, True, 14, 'all-digital'),
    ('Mall Digital Screen', 'mall-digital-screen', 'digital', True, True, 15, 'all-digital'),

    # Static (from adbuq + market)
    ('Static Billboard', 'static-billboard', 'static', False, True, 110, 'all-static'),
    ('Billboards', 'billboards', 'static', False, True, 111, 'all-static'),
    ('Bridge Banner', 'bridge-banner', 'static', False, True, 112, 'all-static'),
    ('Bus Shelter', 'bus-shelter', 'static', False, True, 113, 'all-static'),
    ('Pole Signs', 'pole-signs', 'static', False, True, 114, 'all-static'),
    ('Wall Panels', 'wall-panels', 'static', False, True, 115, 'all-static'),
    ('Hoarding', 'hoarding', 'static', False, True, 116, 'all-static'),
    ('Unipole', 'unipole', 'static', False, True, 117, 'all-static'),
    ('Gantry', 'gantry', 'static', False, True, 118, 'all-static'),
    ('Rooftop Billboard', 'rooftop-billboard', 'static', False, True, 119, 'all-static'),
    ('Wallscape', 'wallscape', 'static', False, True, 120, 'all-static'),

    # Place-based & transit (standalone selectable)
    ('Airport Advertising', 'airport-advertising', 'place', False, True, 200, None),
    ('Mall Advertising', 'mall-advertising', 'place', False, True, 201, None),
    ('Cinema Advertising', 'cinema-advertising', 'place', False, True, 202, None),
    ('Metro Station Advertising', 'metro-station-advertising', 'place', False, True, 203, None),
    ('Railway Platform Advertising', 'railway-platform-advertising', 'place', False, True, 204, None),

    # Transit / mobile
    ('Vehicle Branding', 'vehicle-branding', 'transit', False, True, 300, None),
    ('Bus Wrap', 'bus-wrap', 'transit', False, True, 301, None),
    ('Taxi Branding', 'taxi-branding', 'transit', False, True, 302, None),
    ('Mopy', 'mopy', 'transit', False, True, 303, None),
]

CATEGORY_LABELS = {
    'digital': 'Digital',
    'static': 'Static',
    'place': 'Place Based',
    'transit': 'Transit & Mobile',
    'other': 'Other',
}
