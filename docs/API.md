# MeterRide Backend API Documentation

This document describes the active baseline endpoints currently implemented on the `main` branch of the MeterRide backend service.

---

## Base URLs

- **Local Development**: `http://localhost:8000`
- **Interactive OpenAPI Documentation (Swagger)**: `http://localhost:8000/docs`
- **Alternative API Reference (ReDoc)**: `http://localhost:8000/redoc`

---

## Implemented Endpoints

### 1. Root Welcome

Returns service identity and API version.

- **URL**: `/`
- **Method**: `GET`
- **Authentication**: None
- **Query Parameters**: None
- **Request Body**: None

#### Successful Response (`200 OK`)

```json
{
  "message": "Welcome to MeterRide API",
  "version": "0.1.0"
}
```

---

### 2. Health Check

Health check probe for uptime monitoring, load balancers, and container orchestrators.

- **URL**: `/health`
- **Method**: `GET`
- **Authentication**: None
- **Query Parameters**: None
- **Request Body**: None

#### Successful Response (`200 OK`)

```json
{
  "status": "ok",
  "service": "meterride-backend"
}
```

---

## Planned Modules

The following feature domains will be implemented across subsequent development sprints by the backend team using dedicated feature branches:

1. **Authentication & Users** (User registration, login, JWT validation, roles: Rider, Driver, Admin)
2. **Drivers & Vehicles** (Driver profiles, vehicle registration, status management, verification)
3. **Location** (Real-time telemetry, geofencing, driver coordinate updates)
4. **Fare Estimation** (Dynamic pricing engine, distance/duration metrics, surge calculation)
5. **Ride Booking** (Ride requests, quotes, route definition, scheduling)
6. **Driver Matching** (Geospatial proximity matching, dispatch algorithms, request broadcast)
7. **Trip Lifecycle** (Pickup verification, start trip, route tracking, trip completion)
8. **Payments** (Fare calculation settlement, payment gateway integration, transaction records)
9. **Notifications** (Push notifications, SMS/Email dispatch for trip updates)
10. **Ratings** (Mutual rating system, driver and rider feedback)
11. **Safety** (SOS emergency alerts, ride sharing link, incident reporting)
12. **Admin** (System dashboard, audit logs, dispute handling, user management)
