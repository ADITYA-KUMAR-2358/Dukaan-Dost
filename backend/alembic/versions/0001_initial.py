"""Initial schema for a single local shop."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("selling_price", sa.Float(), nullable=True),
        sa.Column("unit_cost", sa.Float(), nullable=True),
        sa.Column("current_stock", sa.Float(), nullable=True),
        sa.Column("incoming_qty", sa.Float(), nullable=False),
        sa.Column("min_stock", sa.Float(), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("pack_size", sa.Integer(), nullable=True),
        sa.Column("moq", sa.Integer(), nullable=True),
        sa.Column("supplier_name", sa.String(200), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("shop_id", "sku", name="uq_product_shop_sku"),
    )
    op.create_index("ix_products_shop_id", "products", ["shop_id"])
    op.create_table(
        "import_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("encoding", sa.String(40), nullable=False),
        sa.Column("delimiter", sa.String(8), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("accepted_rows", sa.Integer(), nullable=False),
        sa.Column("rejected_rows", sa.Integer(), nullable=False),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False),
        sa.Column("assumptions_json", sa.Text(), nullable=False),
        sa.Column("issues_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("shop_id", "content_hash", name="uq_import_hash"),
    )
    op.create_index("ix_import_batches_shop_id", "import_batches", ["shop_id"])
    op.create_table(
        "sale_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_batch_id", sa.String(36), sa.ForeignKey("import_batches.id", ondelete="SET NULL")),
        sa.Column("invoice_number", sa.String(80), nullable=True),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("returned_quantity", sa.Float(), nullable=False),
        sa.Column("selling_price", sa.Float(), nullable=True),
        sa.Column("unit_cost", sa.Float(), nullable=True),
        sa.Column("discount", sa.Float(), nullable=True),
        sa.Column("stockout", sa.Boolean(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.UniqueConstraint("shop_id", "fingerprint", name="uq_sale_fingerprint"),
    )
    op.create_index("ix_sale_lines_shop_id", "sale_lines", ["shop_id"])
    op.create_index("ix_sale_lines_product_id", "sale_lines", ["product_id"])
    op.create_index("ix_sale_lines_sale_date", "sale_lines", ["sale_date"])
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movement_type", sa.String(40), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("note", sa.String(400), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_inventory_movements_shop_id", "inventory_movements", ["shop_id"])
    op.create_index("ix_inventory_movements_product_id", "inventory_movements", ["product_id"])
    op.create_table(
        "forecast_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("error_code", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_forecast_runs_shop_id", "forecast_runs", ["shop_id"])
    op.create_table(
        "forecast_points",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("predicted_qty", sa.Float(), nullable=False),
        sa.Column("baseline_qty", sa.Float(), nullable=False),
        sa.Column("model_id", sa.String(80), nullable=False),
        sa.Column("baseline_id", sa.String(80), nullable=False),
    )
    op.create_index("ix_forecast_points_run_id", "forecast_points", ["run_id"])
    op.create_index("ix_forecast_points_product_id", "forecast_points", ["product_id"])
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("forecast_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reorder_point", sa.Float(), nullable=True),
        sa.Column("safety_stock", sa.Float(), nullable=True),
        sa.Column("lead_time_demand", sa.Float(), nullable=True),
        sa.Column("suggested_qty", sa.Float(), nullable=True),
        sa.Column("policy", sa.String(80), nullable=False),
        sa.Column("slow_status", sa.String(80), nullable=False),
        sa.Column("flags_json", sa.Text(), nullable=False),
        sa.Column("facts_json", sa.Text(), nullable=False),
        sa.Column("user_qty", sa.Float(), nullable=True),
        sa.Column("user_note", sa.String(400), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendations_shop_id", "recommendations", ["shop_id"])
    op.create_index("ix_recommendations_product_id", "recommendations", ["product_id"])
    op.create_index("ix_recommendations_run_id", "recommendations", ["run_id"])
    op.create_table(
        "app_settings",
        sa.Column("shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("service_level", sa.Float(), nullable=False),
        sa.Column("coverage_days", sa.Integer(), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("prefer_tabpfn", sa.Boolean(), nullable=False),
        sa.Column("ollama_model", sa.String(120), nullable=False),
    )
    op.create_table(
        "workspace_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active_shop_id", sa.String(36), sa.ForeignKey("shops.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("workspace_state")
    op.drop_table("app_settings")
    op.drop_table("recommendations")
    op.drop_table("forecast_points")
    op.drop_table("forecast_runs")
    op.drop_table("inventory_movements")
    op.drop_table("sale_lines")
    op.drop_table("import_batches")
    op.drop_table("products")
    op.drop_table("shops")
