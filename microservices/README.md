## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+

### Run the System
```bash
# Clone and navigate
git clone <your-repo>
cd microservices

# Start all services
docker-compose up --build

# The system will be available at:
# API Gateway: http://localhost:8000
# NATS: localhost:4222
# PostgreSQL: localhost:5433
```

## 🧪 Test the EDA System

### 1. Create an Order (Event-Driven)
```bash
curl -X POST http://localhost:8000/orders/create \
  -H "Content-Type: application/json" \
  -d '{"item_id": 1, "quantity": 2, "price": 19.99}'
```

### 2. Monitor Events
```bash
# View all events
curl http://localhost:8000/events

# View events by type
curl http://localhost:8000/events/order.created

# View events by correlation ID
curl http://localhost:8000/events/correlation/{correlation_id}
```

## 🔄 Event Flow

1. **Client Request** → API Gateway
2. **Event Publishing** → NATS Event Bus
3. **Service Processing** → Orders Service consumes events
4. **Follow-up Events** → Inventory updates, notifications
5. **Event Storage** → Complete audit trail

## ��️ Services

- **API Gateway**: Event coordinator and publisher
- **Orders Service**: Order processing and event consumer
- **Products Service**: Inventory management via events
- **Notifications Service**: Event-driven notifications
- **Event Store**: Complete event history and replay

## 🎯 Key Features

- ✅ **Zero HTTP dependencies** between services
- ✅ **Real-time event monitoring**
- ✅ **Event correlation tracking**
- ✅ **Complete audit trails**
- ✅ **Service independence**
- ✅ **Scalable architecture**

## �� Why EDA?

- **Scalability**: Services can scale independently
- **Resilience**: Service failures don't cascade
- **Performance**: Asynchronous processing
- **Maintainability**: Loose coupling, easy to modify
- **Observability**: Complete system visibility

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **NATS**: High-performance messaging system
- **PostgreSQL**: Reliable data storage
- **Docker**: Containerized deployment
- **Pydantic**: Data validation and serialization

## 📚 Learning Path

This project demonstrates:
1. **Event-Driven Architecture** fundamentals
2. **Microservices** best practices
3. **Asynchronous communication** patterns
4. **Event sourcing** and audit trails
5. **Service orchestration** with Docker

## 🔮 Next Steps

- **Event replay** capabilities
- **CQRS pattern** implementation
- **Saga pattern** for distributed transactions
- **Production monitoring** with Prometheus/Grafana
- **Event versioning** and schema evolution

## �� Contributing

This is a learning project. Feel free to:
- Fork and experiment
- Add new event types
- Implement additional services
- Enhance monitoring capabilities

## 📄 License

MIT License - Use this code to learn and build amazing EDA systems!

---

**Built with ❤️ in 6 hours of intense coding and learning! in Santa Marta over the caribbean ocean!**