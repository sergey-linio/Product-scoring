sql_text = '''
    SELECT
    catalog_config.sku,
    id_catalog_config,
    short_description,
    catalog_config.name AS title,
    catalog_brand.name AS brand,
    catalog_config.description AS description

    FROM catalog_config
    JOIN catalog_brand ON catalog_config.fk_catalog_brand = catalog_brand.id_catalog_brand
    WHERE catalog_config.id_catalog_config = {}'''

sql_image = '''
    SELECT
    catalog_config.id_catalog_config,
    catalog_brand.url_key,
    COUNT(catalog_config.id_catalog_config) AS image_count

    FROM catalog_config
    JOIN catalog_product_image ON catalog_config.id_catalog_config = catalog_product_image.fk_catalog_config
    JOIN catalog_brand ON catalog_config.fk_catalog_brand = catalog_brand.id_catalog_brand
    WHERE catalog_config.id_catalog_config = {}'''

sql_category = '''
    SELECT
    catalog_config.id_catalog_config,
    COUNT(*) AS category_count

    FROM catalog_config
    JOIN catalog_config_has_catalog_category ON catalog_config.id_catalog_config = catalog_config_has_catalog_category.fk_catalog_config
    JOIN catalog_category ON catalog_config_has_catalog_category.fk_catalog_category = catalog_category.id_catalog_category
    WHERE catalog_config.id_catalog_config = {}
    GROUP BY id_catalog_config AND catalog_category.status = "active"'''

sql_negative = '''
    SELECT
    catalog_config.sku,
    id_catalog_config,
    short_description,
    catalog_config.name AS title,
    catalog_brand.name AS brand,
    catalog_config.description AS description

    FROM catalog_config
    JOIN catalog_brand ON catalog_config.fk_catalog_brand = catalog_brand.id_catalog_brand
    WHERE catalog_config.id_catalog_config = {}'''

sql_weights = '''
    SELECT catalog_category.id_catalog_category
    FROM catalog_config
    JOIN catalog_config_has_catalog_category ON catalog_config.id_catalog_config = catalog_config_has_catalog_category.fk_catalog_config
    JOIN catalog_category ON catalog_config_has_catalog_category.fk_catalog_category = catalog_category.id_catalog_category
    WHERE catalog_config.id_catalog_config = {} AND catalog_category.status = "active"
    '''