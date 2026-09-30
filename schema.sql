CREATE TABLE users (
    user_id int GENERATED ALWAYS AS IDENTITY primary key,
    username text unique NOT NULL,
    password_hash text NOT NULL,
    first_name text NOT NULL,
    last_name text NOT NULL,
    created_at timestamp NOT NULL DEFAULT now()
);

CREATE TABLE manifests (
    manifest_id int GENERATED ALWAYS AS IDENTITY primary key,
    purchase_date date NOT NULL,
    cost numeric(10, 2) NOT NULL,
    entered_by int NOT NULL references users(user_id)
);

CREATE TABLE products (
    product_id int GENERATED ALWAYS AS IDENTITY primary key,
    manifest_id int NOT NULL references manifests(manifest_id),
    barcode text NOT NULL,
    product_name text NOT NULL,
    retail_price numeric(10, 2) NOT NULL,
    list_price numeric(10, 2) NOT NULL,
    status text NOT NULL CHECK (status IN ('available', 'sold', 'not_available', 'deleted')),
    sold_price numeric(10, 2) NULL,
    sold_at timestamp NULL
);

CREATE INDEX idx_products_manifest_id ON products (manifest_id);
CREATE INDEX idx_products_status ON products (status);
CREATE INDEX idx_products_barcode ON products (barcode);
