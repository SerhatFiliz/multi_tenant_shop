# NexusCommerce Core (Marketplace & Tenant Engine) 🏢

The **NexusCommerce Core** is the robust, high-traffic "Body" of our B2B SaaS ecosystem. Built with Django, it provides an enterprise-ready Multi-Tenant Architecture that enables thousands of SMEs to operate isolated, custom storefronts while simultaneously feeding a global marketplace aggregator.

---

## 🛠️ Tech Stack

- **Framework**: Django 5.x
- **Database**: PostgreSQL (Leveraging Postgres schemas for isolation)
- **Multi-Tenancy**: `django-tenants`
- **Asynchronous Tasks**: Celery (Simulated) & Redis
- **Styling**: Tailwind CSS & Glassmorphism UI
- **Search**: Elasticsearch Integration

---

## ✨ Key Features

### 1. 'Trendyol-Style' Global Marketplace Aggregator
The public schema (`public_home.html`) serves as a unified mega-marketplace. It queries active inventory across all SME schemas in real-time, allowing customers to discover products globally while routing them to the specific tenant's domain for checkout.

### 2. Isolated Multi-Tenant Database Schemas
Data privacy and integrity are paramount for SMEs. Using `django-tenants`, every store gets its own dedicated PostgreSQL schema. This ensures zero data leakage between competitors and allows for massive horizontal scaling.

### 3. Live Chat Override (Human Handoff)
While our AI Brain handles customer support by default, store owners need control. The Nexus-Admin dashboard features a seamless **Live Chat Override** toggle. When activated, the AI immediately steps back, routing WebSockets directly to the human store owner for VIP customer service.

### 4. Webhook Triggers for AI Synchronization
To keep the decoupled AI Brain perfectly in sync, the Django core fires background HTTP Webhooks (`/api/v1/webhooks/store-event`) upon critical state changes—such as order placements or stock depletions. This ensures the AI always has the latest context without burdening the primary transactional database.

---

## 🔗 Architecture Link
This repository handles the **transactional e-commerce layer**. For details on the intelligence and analytics layer, please see the [Nexus AI Brain (FastAPI) Repository](../saas_ecommerce_ai_agent/README.md).
