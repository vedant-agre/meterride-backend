# MeterRide Phase 01 — Frozen API Contract & Specification

**Document Version:** `1.0.0-FROZEN`  
**Status:** FROZEN BASELINE CONTRACT  
**Target Phase:** Phase 01 — Core Ride Booking & Mobility Flow  

---

## 1. Executive Summary & Phase 01 Scope

MeterRide is a Smart Mobility / Ride Booking Platform designed for scalable, asynchronous microservice-ready backend execution. This document defines the **Frozen API Contract** for Phase 01.

### 1.1 Phase 01 Lifecycle Flow
The primary objective of Phase 01 is to establish an end-to-end, functional ride-booking lifecycle:

```
[ Rider ]
   │
   ├── 1. Register / Login
   ├── 2. Input Pickup & Destination Coordinates
   ├── 3. Get Real-Time Fare Estimate
   ├── 4. Request Ride
   │
[ Matching Engine (Rule-Based) ]
   │
   ├── 5. Query Candidate Available Drivers (Nearby)
   │
[ Driver ]
   │
   ├── 6. Driver Accepts Assignment
   ├── 7. Driver Arriving ──> Driver Arrived
   ├── 8. OTP Verification (Rider -> Driver -> Backend)
   ├── 9. Trip In Progress
   ├── 10. Trip Completed
   │
[ Settlement & Feedback ]
   │
   ├── 11. Mock Payment Processing (CASH / UPI / CARD)
   ├── 12. Mutual Rating (Rider <──> Driver)
   └── 13. Stored in Ride History
```

---

## 2. Architecture & Layering Conventions

MeterRide enforces a strict 3-tier unidirectional design pattern across all modules:

```
HTTP Request
     │
     ▼
[ Routers Layer ] (app/routers/)
     │  - Handles HTTP status codes, request parsing, parameter validation
     │  - Enforces JWT authentication & role-based access control (RBAC)
     │  - MUST NOT contain business calculations or direct SQL queries
     ▼
[ Services Layer ] (app/services/)
     │  - Encapsulates all domain rules, state machines, and calculations
     │  - Coordinates database transactions via Session
     │  - Independent of FastAPI/HTTP request context
     ▼
[ Database Layer ] (app/models/, app/database/)
     │  - SQLAlchemy 2.x Declarative Models inheriting from Base
     │  - Persistent storage, constraints, indexes, foreign keys
     ▼
PostgreSQL Engine
```

### Schemas (`app/schemas/`)
- Pure Pydantic v2 schemas for all request payloads and response serialization.
- Models must never be leaked directly to the client without schema mapping.

---

## 3. Global HTTP & API Conventions

### 3.1 Authentication & Authorization Header
All protected endpoints require a standard HTTP Authorization Bearer token:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

### 3.2 User Roles
- `RIDER`: Standard consumer requesting rides.
- `DRIVER`: Vehicle operator offering transport services.
- `ADMIN`: Platform operator with system oversight privileges.

### 3.3 HTTP Status Codes
- `200 OK`: Successful retrieval or state modification (`GET`, `PATCH`, `PUT`).
- `201 Created`: Successful entity creation (`POST`).
- `204 No Content`: Successful deletion without response body (`DELETE`).
- `400 Bad Request`: Business rule violation or invalid state transition.
- `401 Unauthorized`: Missing, expired, or invalid JWT access token.
- `403 Forbidden`: Authenticated user lacks the necessary role permissions.
- `404 Not Found`: Target resource does not exist.
- `409 Conflict`: Unique constraint violation (e.g., email/phone/vehicle reg already registered).
- `422 Unprocessable Entity`: Request body or query parameters failed schema validation.

### 3.4 Standard Error Response Format
```json
{
  "detail": "Error description or validation message"
}
```

---

## 4. Database Schema Entities & Relationships

```
 ┌──────────────┐          1:1          ┌──────────────┐
 │     User     │───────────────────────│    Driver    │
 └──────┬───────┘                       └──────┬───────┘
        │                                      │
        │ 1:N (as rider)                       │ 1:N (as owner)
        │                                      ▼
        │                               ┌──────────────┐
        │                               │   Vehicle    │
        │                               └──────┬───────┘
        │                                      │ 1:N
        ▼                                      ▼
 ┌─────────────────────────────────────────────────────┐
 │                        Ride                         │
 └──────┬───────────────────┬───────────────────┬──────┘
        │ 1:1               │ 1:N               │ 1:N
        ▼                   ▼                   ▼
 ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
 │   Payment    │    │    Rating    │    │SafetyIncident│
 └──────────────┘    └──────────────┘    └──────────────┘

 ┌──────────────┐
 │ Notification │ (Belongs to User, optional Ride FK)
 └──────────────┘
```

### 4.1 User
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique user identifier |
| `name` | String(100) | Not Null | Full legal name |
| `email` | String(255) | Unique, Index, Not Null | Unique email address |
| `phone` | String(20) | Unique, Index, Not Null | Contact phone number |
| `password_hash`| String(255) | Not Null | Bcrypt password hash |
| `role` | Enum | `RIDER`, `DRIVER`, `ADMIN` | User access role |
| `is_active` | Boolean | Default `True` | Account status flag |
| `created_at` | DateTime(UTC)| Default current timestamp | Account creation timestamp |
| `updated_at` | DateTime(UTC)| Default current timestamp, auto update | Last profile update |

### 4.2 Driver
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique driver identifier |
| `user_id` | UUID | FK -> `User.id`, Unique, Not Null | Reference to associated User account |
| `license_number`| String(50)| Unique, Index, Not Null | Commercial driving license ID |
| `status` | Enum | `OFFLINE`, `AVAILABLE`, `BUSY` | Current operational availability |
| `current_latitude`| Decimal(9,6)| Nullable | Driver's last reported latitude |
| `current_longitude`| Decimal(9,6)| Nullable | Driver's last reported longitude |
| `rating_average`| Decimal(3,2)| Default `5.00` | Aggregate driver rating |
| `total_rides` | Integer | Default `0` | Total completed trips count |
| `created_at` | DateTime(UTC)| Default current timestamp | Driver registration timestamp |

> **Note on Location Tracking:** Driver's current location is updated directly on the `Driver` table. No separate location-history telemetry table is created in Phase 01.

### 4.3 Vehicle
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique vehicle identifier |
| `driver_id` | UUID | FK -> `Driver.id`, Not Null | Owning driver ID |
| `vehicle_type` | Enum | `BIKE`, `AUTO`, `SEDAN`, `SUV` | Vehicle categorization |
| `registration_number`| String(50)| Unique, Index, Not Null | Official license plate / registration |
| `model` | String(100) | Not Null | Vehicle model (e.g. "Honda City", "Bajaj Auto") |
| `color` | String(50) | Not Null | Vehicle exterior color |
| `capacity` | Integer | Not Null | Passenger seating capacity |
| `is_active` | Boolean | Default `True` | Active fleet status |

### 4.4 Ride
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique ride identifier |
| `rider_id` | UUID | FK -> `User.id`, Not Null | Rider who booked the trip |
| `driver_id` | UUID | FK -> `Driver.id`, Nullable | Assigned driver (set once assigned) |
| `vehicle_id` | UUID | FK -> `Vehicle.id`, Nullable | Vehicle assigned for the trip |
| `pickup_latitude` | Decimal(9,6) | Not Null | Starting point latitude |
| `pickup_longitude`| Decimal(9,6) | Not Null | Starting point longitude |
| `pickup_address` | String(255) | Not Null | Human-readable pickup location |
| `drop_latitude` | Decimal(9,6) | Not Null | Destination latitude |
| `drop_longitude` | Decimal(9,6) | Not Null | Destination longitude |
| `drop_address` | String(255) | Not Null | Human-readable destination |
| `vehicle_type` | Enum | `BIKE`, `AUTO`, `SEDAN`, `SUV` | Requested vehicle tier |
| `status` | Enum | See State Machine below | Current ride state |
| `estimated_distance`| Decimal(8,2) | Not Null | Distance in Kilometers |
| `estimated_duration`| Integer | Not Null | Duration in Minutes |
| `estimated_fare` | Decimal(10,2)| Not Null | Quoted fare in currency units |
| `final_fare` | Decimal(10,2)| Nullable | Final charged fare upon completion |
| `otp` | String(6) | Not Null | 4 or 6-digit trip start verification code |
| `requested_at` | DateTime(UTC)| Default current timestamp | Booking request time |
| `started_at` | DateTime(UTC)| Nullable | Trip start timestamp |
| `completed_at` | DateTime(UTC)| Nullable | Trip completion timestamp |
| `cancelled_at` | DateTime(UTC)| Nullable | Trip cancellation timestamp |

### 4.5 Payment
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique payment transaction ID |
| `ride_id` | UUID | FK -> `Ride.id`, Unique, Not Null | Associated completed ride |
| `amount` | Decimal(10,2)| Not Null | Final transaction amount |
| `method` | Enum | `CASH`, `UPI`, `CARD` | Payment settlement method |
| `status` | Enum | `PENDING`, `SUCCESS`, `FAILED` | Payment transaction status |
| `transaction_id`| String(100)| Nullable | Mock reference/gateway transaction ID |
| `created_at` | DateTime(UTC)| Default current timestamp | Timestamp of payment record |

### 4.6 Rating
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique rating record ID |
| `ride_id` | UUID | FK -> `Ride.id`, Not Null | Reference to completed ride |
| `from_user_id` | UUID | FK -> `User.id`, Not Null | User submitting the review |
| `to_user_id` | UUID | FK -> `User.id`, Not Null | User receiving the review |
| `rating` | Integer | Check (1 <= rating <= 5) | Integer score from 1 to 5 |
| `comment` | String(500) | Nullable | Optional written feedback |
| `created_at` | DateTime(UTC)| Default current timestamp | Rating timestamp |

### 4.7 Notification
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique notification ID |
| `user_id` | UUID | FK -> `User.id`, Not Null | Recipient user |
| `ride_id` | UUID | FK -> `Ride.id`, Nullable | Related ride entity |
| `type` | String(50) | Not Null | Event type (e.g., `DRIVER_ASSIGNED`) |
| `title` | String(100) | Not Null | Short notification headline |
| `message` | String(255) | Not Null | Human-readable notification body |
| `is_read` | Boolean | Default `False` | Acknowledgment status |
| `created_at` | DateTime(UTC)| Default current timestamp | Notification generated timestamp |

### 4.8 SafetyIncident
| Field | Type | Modifiers / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key, default UUID4 | Unique safety event ID |
| `ride_id` | UUID | FK -> `Ride.id`, Not Null | Associated active/recent ride |
| `reported_by` | UUID | FK -> `User.id`, Not Null | User lodging the incident/SOS |
| `type` | String(50) | Not Null | Incident category (e.g., `SOS_TRIGGER`, `ROUTE_DEVIATION`) |
| `description` | String(1000)| Not Null | Detailed description of the event |
| `status` | Enum | `OPEN`, `RESOLVED` | Audit/Safety team resolution status |
| `created_at` | DateTime(UTC)| Default current timestamp | Incident report timestamp |

---

## 5. Ride Lifecycle State Machine

The ride lifecycle is strictly regulated. Any state transition violating this diagram must return `400 Bad Request`.

```
                    ┌──────────────┐
                    │  REQUESTED   │
                    └──────┬───────┘
                           │ (System starts matching)
                           ▼
                    ┌──────────────┐
       ┌───────────>│  SEARCHING   │────────────┐
       │ (Retry)    └──────┬───────┘            │ (No available driver)
       │                   │ (Driver assigned)  ▼
       │                   ▼             ┌──────────────┐
       │            ┌──────────────┐     │  NO_DRIVER   │
       │            │DRIVER_ASSIGNED│    └──────────────┘
       │            └──────┬───────┘
       │                   │ (Driver starts navigating to pickup)
       │                   ▼
       │            ┌──────────────┐
       │            │DRIVER_ARRIVING│
       │            └──────┬───────┘
       │                   │ (Driver arrives at pickup spot)
       │                   ▼
       │            ┌──────────────┐
       │            │DRIVER_ARRIVED│
       │            └──────┬───────┘
       │                   │ (Rider OTP verified)
       │                   ▼
       │            ┌──────────────┐
       │            │ IN_PROGRESS  │
       │            └──────┬───────┘
       │                   │ (Driver ends trip at destination)
       │                   ▼
       │            ┌──────────────┐
       │            │  COMPLETED   │
       │            └──────────────┘
       │
       │ (Cancellation allowed prior to OTP verification)
       └───────────────────┬───────────────────┐
                           ▼                   ▼
                    ┌──────────────┐    ┌──────────────┐
                    │  CANCELLED   │    │  (Rejected)  │
                    └──────────────┘    └──────────────┘
```

### Transition Matrix & Rules:
- **`REQUESTED`** ──> `SEARCHING`, `CANCELLED`
- **`SEARCHING`** ──> `DRIVER_ASSIGNED`, `NO_DRIVER`, `CANCELLED`
- **`DRIVER_ASSIGNED`** ──> `DRIVER_ARRIVING`, `CANCELLED`, `SEARCHING` (if driver rejects/cancels)
- **`DRIVER_ARRIVING`** ──> `DRIVER_ARRIVED`, `CANCELLED`
- **`DRIVER_ARRIVED`** ──> `IN_PROGRESS` (Requires successful `/verify-otp`), `CANCELLED`
- **`IN_PROGRESS`** ──> `COMPLETED`
- **Terminal States**: `COMPLETED`, `CANCELLED`, `NO_DRIVER` (No further transitions permitted)

---

## 6. Complete API Specifications (12 Modules)

---

### Module 1: Authentication & Users

#### 1.1 `POST /auth/register`
- **Purpose**: Register a new user account (default role: `RIDER`).
- **Auth**: None
- **Role Required**: Public
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+919876543210",
    "password": "SecurePassword123!",
    "role": "RIDER"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "+919876543210",
      "role": "RIDER",
      "is_active": true,
      "created_at": "2026-09-23T12:00:00Z"
    }
    ```
  - `409 Conflict`: Email or phone number already registered.
  - `422 Unprocessable Entity`: Password too short or invalid email format.

#### 1.2 `POST /auth/login`
- **Purpose**: Authenticate user credentials and issue a JWT access token.
- **Auth**: None
- **Role Required**: Public
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "role": "RIDER"
      }
    }
    ```
  - `401 Unauthorized`: Invalid email or password.

#### 1.3 `GET /users/me`
- **Purpose**: Retrieve profile details of currently authenticated user.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "+919876543210",
      "role": "RIDER",
      "is_active": true,
      "created_at": "2026-09-23T12:00:00Z",
      "updated_at": "2026-09-23T12:00:00Z"
    }
    ```
  - `401 Unauthorized`: Missing or invalid token.

#### 1.4 `PATCH /users/me`
- **Purpose**: Update current authenticated user's name or phone number.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Request Body**:
  ```json
  {
    "name": "Jane Smith",
    "phone": "+919876543299"
  }
  ```
- **Responses**:
  - `200 OK`: Returns updated user object.
  - `409 Conflict`: Phone number already in use.

---

### Module 2: Drivers

#### 2.1 `POST /drivers/register`
- **Purpose**: Create a Driver profile linked to the authenticated user account and elevate user role to `DRIVER`.
- **Auth**: Bearer Token
- **Role Required**: `RIDER` or `DRIVER`
- **Request Body**:
  ```json
  {
    "license_number": "DL-MH-12-20240001234"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "license_number": "DL-MH-12-20240001234",
      "status": "OFFLINE",
      "current_latitude": null,
      "current_longitude": null,
      "rating_average": 5.0,
      "total_rides": 0,
      "created_at": "2026-09-23T12:10:00Z"
    }
    ```
  - `409 Conflict`: Driver profile or license number already exists for user.

#### 2.2 `GET /drivers/me`
- **Purpose**: Return current driver's profile and active statistics.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Responses**:
  - `200 OK`: Returns driver object.
  - `404 Not Found`: Authenticated user does not have an associated driver profile.

#### 2.3 `PATCH /drivers/me`
- **Purpose**: Update driver-specific details (e.g., license update).
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Request Body**:
  ```json
  {
    "license_number": "DL-MH-12-20240009999"
  }
  ```
- **Responses**:
  - `200 OK`: Returns updated driver object.

#### 2.4 `PATCH /drivers/status`
- **Purpose**: Change driver availability state.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Request Body**:
  ```json
  {
    "status": "AVAILABLE"
  }
  ```
- **Allowed Statuses**: `OFFLINE`, `AVAILABLE`, `BUSY`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "AVAILABLE"
    }
    ```
  - `400 Bad Request`: Invalid status value or cannot go available without active vehicle.

---

### Module 3: Vehicles

#### 3.1 `POST /vehicles`
- **Purpose**: Register a new vehicle owned by the authenticated driver.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Request Body**:
  ```json
  {
    "vehicle_type": "SEDAN",
    "registration_number": "MH12AB1234",
    "model": "Hyundai Verna",
    "color": "White",
    "capacity": 4
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "e2c34a1b-9f64-4e4b-9801-1e96a4a75412",
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "vehicle_type": "SEDAN",
      "registration_number": "MH12AB1234",
      "model": "Hyundai Verna",
      "color": "White",
      "capacity": 4,
      "is_active": true
    }
    ```
  - `409 Conflict`: Registration number already registered.

#### 3.2 `GET /vehicles`
- **Purpose**: List all vehicles registered under the authenticated driver.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Responses**:
  - `200 OK`: Returns array of `Vehicle` objects.

#### 3.3 `GET /vehicles/{vehicle_id}`
- **Purpose**: Get details of a specific vehicle.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (must be owner) or `ADMIN`
- **Responses**:
  - `200 OK`: Returns `Vehicle` object.
  - `403 Forbidden`: Driver does not own this vehicle.
  - `404 Not Found`: Vehicle not found.

#### 3.4 `PATCH /vehicles/{vehicle_id}`
- **Purpose**: Update vehicle properties (color, model, active status).
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (must be owner)
- **Request Body**:
  ```json
  {
    "color": "Silver",
    "is_active": true
  }
  ```
- **Responses**:
  - `200 OK`: Returns updated `Vehicle` object.
  - `403 Forbidden`: Driver does not own this vehicle.

#### 3.5 `DELETE /vehicles/{vehicle_id}`
- **Purpose**: Soft delete or deactivate a vehicle owned by the driver.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (must be owner)
- **Responses**:
  - `204 No Content`: Deletion successful.
  - `400 Bad Request`: Cannot delete vehicle assigned to an active trip.

---

### Module 4: Location

#### 4.1 `POST /drivers/location`
- **Purpose**: Update the driver's current coordinates.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Request Body**:
  ```json
  {
    "latitude": 18.520430,
    "longitude": 73.856744
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "latitude": 18.520430,
      "longitude": 73.856744,
      "updated_at": "2026-09-23T12:15:00Z"
    }
    ```

#### 4.2 `GET /drivers/nearby`
- **Purpose**: Retrieve available drivers within a specified geographic radius.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `ADMIN`
- **Query Parameters**:
  - `latitude` (float, required): Search center latitude (e.g. `18.520430`)
  - `longitude` (float, required): Search center longitude (e.g. `73.856744`)
  - `radius_km` (float, optional, default `5.0`): Search radius in kilometers
  - `vehicle_type` (string, optional): Filter by `BIKE`, `AUTO`, `SEDAN`, `SUV`
- **Responses**:
  - `200 OK`:
    ```json
    [
      {
        "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "John Driver",
        "latitude": 18.524500,
        "longitude": 73.852100,
        "distance_km": 0.65,
        "rating_average": 4.85,
        "vehicle": {
          "vehicle_type": "SEDAN",
          "model": "Hyundai Verna",
          "registration_number": "MH12AB1234"
        }
      }
    ]
    ```

---

### Module 5: Fare Estimation

#### 5.1 `POST /rides/estimate`
- **Purpose**: Calculate distance, duration, and fare breakdown before booking.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`
- **Request Body**:
  ```json
  {
    "pickup_latitude": 18.520430,
    "pickup_longitude": 73.856744,
    "drop_latitude": 18.591200,
    "drop_longitude": 73.738900,
    "vehicle_type": "SEDAN"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "distance_km": 14.2,
      "estimated_duration_minutes": 32,
      "vehicle_type": "SEDAN",
      "fare_breakdown": {
        "base_fare": 50.00,
        "distance_fare": 170.40,
        "time_fare": 32.00,
        "estimated_total_fare": 252.40
      }
    }
    ```
  - `400 Bad Request`: Pickup and drop coordinates identical or out of range.

---

### Module 6: Ride Booking & Lifecycle

#### 6.1 `POST /rides`
- **Purpose**: Create a new ride request and generate trip verification OTP.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`
- **Request Body**:
  ```json
  {
    "pickup_latitude": 18.520430,
    "pickup_longitude": 73.856744,
    "pickup_address": "Shivajinagar, Pune",
    "drop_latitude": 18.591200,
    "drop_longitude": 73.738900,
    "drop_address": "Hinjawadi Phase 1, Pune",
    "vehicle_type": "SEDAN"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "rider_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "driver_id": null,
      "vehicle_id": null,
      "pickup_address": "Shivajinagar, Pune",
      "drop_address": "Hinjawadi Phase 1, Pune",
      "vehicle_type": "SEDAN",
      "status": "REQUESTED",
      "estimated_distance": 14.2,
      "estimated_duration": 32,
      "estimated_fare": 252.40,
      "otp": "4821",
      "requested_at": "2026-09-23T12:20:00Z"
    }
    ```
  - `400 Bad Request`: Rider already has an active ongoing ride.

#### 6.2 `GET /rides/{ride_id}`
- **Purpose**: Get comprehensive details of a specific ride.
- **Auth**: Bearer Token
- **Role Required**: Assigned `RIDER`, Assigned `DRIVER`, or `ADMIN`
- **Responses**:
  - `200 OK`: Returns full `Ride` representation including driver/vehicle details if assigned.
  - `403 Forbidden`: Requester is neither the rider, assigned driver, nor admin.
  - `404 Not Found`: Ride ID does not exist.

#### 6.3 `GET /rides/my-rides`
- **Purpose**: Retrieve historical list of rides for the authenticated user (as Rider or Driver).
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`
- **Query Parameters**:
  - `status` (string, optional): Filter by ride status (e.g. `COMPLETED`, `CANCELLED`)
  - `limit` (int, default `20`)
  - `offset` (int, default `0`)
- **Responses**:
  - `200 OK`: Returns paginated list of rides.

#### 6.4 `POST /rides/{ride_id}/cancel`
- **Purpose**: Cancel a ride prior to trip commencement.
- **Auth**: Bearer Token
- **Role Required**: Assigned `RIDER`, Assigned `DRIVER`, or `ADMIN`
- **Request Body**:
  ```json
  {
    "reason": "Changed plans"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "status": "CANCELLED",
      "cancelled_at": "2026-09-23T12:25:00Z"
    }
    ```
  - `400 Bad Request`: Ride cannot be cancelled once `IN_PROGRESS` or already `COMPLETED`.

#### 6.5 `PATCH /rides/{ride_id}/status`
- **Purpose**: Transition ride through progressive operational states.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (assigned to ride) or `ADMIN`
- **Request Body**:
  ```json
  {
    "status": "DRIVER_ARRIVING"
  }
  ```
- **Responses**:
  - `200 OK`: Returns updated `Ride` object.
  - `400 Bad Request`: Invalid state transition. (e.g. attempting to move to `IN_PROGRESS` without verifying OTP via `/verify-otp`).

---

### Module 7: Driver Matching

#### 7.1 `GET /matching/{ride_id}/candidates`
- **Purpose**: Calculate and return candidate drivers sorted by proximity and availability for a requested ride.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`, System/Internal
- **Responses**:
  - `200 OK`:
    ```json
    [
      {
        "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "distance_km": 1.2,
        "eta_minutes": 4,
        "rating_average": 4.9
      }
    ]
    ```

#### 7.2 `POST /matching/{ride_id}/assign`
- **Purpose**: Assign a designated driver to a ride, moving status to `DRIVER_ASSIGNED`.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (accepting offer) or `ADMIN`
- **Request Body**:
  ```json
  {
    "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "DRIVER_ASSIGNED"
    }
    ```
  - `409 Conflict`: Ride already assigned to another driver or driver is `BUSY`.

#### 7.3 `POST /matching/{ride_id}/reject`
- **Purpose**: Driver declines the ride broadcast offer.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER`
- **Request Body**:
  ```json
  {
    "reason": "Too far from pickup"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "message": "Ride rejected by driver",
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412"
    }
    ```

#### 7.4 `POST /matching/{ride_id}/retry`
- **Purpose**: Re-trigger matching dispatch if driver rejected or assignment timed out.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `ADMIN`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "status": "SEARCHING"
    }
    ```

---

### Module 8: Payments (Mock Phase 01)

#### 8.1 `POST /payments`
- **Purpose**: Process mock payment settlement for a completed ride.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `ADMIN`
- **Request Body**:
  ```json
  {
    "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
    "amount": 252.40,
    "method": "UPI"
  }
  ```
- **Allowed Methods**: `CASH`, `UPI`, `CARD`
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "amount": 252.40,
      "method": "UPI",
      "status": "SUCCESS",
      "transaction_id": "MOCK-TXN-987654321",
      "created_at": "2026-09-23T13:00:00Z"
    }
    ```
  - `400 Bad Request`: Ride not in `COMPLETED` status or payment already submitted.

#### 8.2 `GET /payments/{payment_id}`
- **Purpose**: Fetch payment receipt by payment transaction ID.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Responses**:
  - `200 OK`: Returns `Payment` record.

#### 8.3 `GET /payments/ride/{ride_id}`
- **Purpose**: Fetch payment record associated with a specific ride.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Responses**:
  - `200 OK`: Returns `Payment` record.
  - `404 Not Found`: No payment record found for ride.

---

### Module 9: Ratings

#### 9.1 `POST /ratings`
- **Purpose**: Submit rating and optional review for the counterpart user on a completed ride.
- **Auth**: Bearer Token
- **Role Required**: `RIDER` or `DRIVER`
- **Request Body**:
  ```json
  {
    "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
    "rating": 5,
    "comment": "Polite driver, clean car, smooth ride."
  }
  ```
- **Validation**: Rating must be an integer between 1 and 5.
- **Responses**:
  - `201 Created`:
    ```json
    {
      "id": "c1a45b78-9e23-4d6a-8b1c-3e7890abcdef",
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "from_user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "to_user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "rating": 5,
      "comment": "Polite driver, clean car, smooth ride.",
      "created_at": "2026-09-23T13:05:00Z"
    }
    ```
  - `400 Bad Request`: User already submitted rating for this ride or ride not completed.

#### 9.2 `GET /users/{user_id}/ratings`
- **Purpose**: Get aggregated score and reviews received by a user.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "rating_average": 4.88,
      "total_reviews": 42,
      "recent_reviews": [
        {
          "rating": 5,
          "comment": "Smooth ride.",
          "created_at": "2026-09-23T13:05:00Z"
        }
      ]
    }
    ```

---

### Module 10: Notifications (Database-Stored Phase 01)

#### 10.1 `GET /notifications`
- **Purpose**: Fetch in-app notifications for the authenticated user.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN`
- **Query Parameters**:
  - `unread_only` (bool, default `false`)
- **Responses**:
  - `200 OK`:
    ```json
    [
      {
        "id": "a89c3d4e-1234-5678-9abc-def012345678",
        "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
        "type": "DRIVER_ARRIVED",
        "title": "Driver Arrived",
        "message": "Your driver has arrived at the pickup spot.",
        "is_read": false,
        "created_at": "2026-09-23T12:35:00Z"
      }
    ]
    ```

#### 10.2 `PATCH /notifications/{notification_id}/read`
- **Purpose**: Mark a specific notification as read.
- **Auth**: Bearer Token
- **Role Required**: `RIDER`, `DRIVER`, `ADMIN` (must be owner)
- **Responses**:
  - `200 OK`:
    ```json
    {
      "id": "a89c3d4e-1234-5678-9abc-def012345678",
      "is_read": true
    }
    ```

---

### Module 11: Safety & Verification

#### 11.1 `POST /rides/{ride_id}/verify-otp`
- **Purpose**: Driver validates rider's OTP to start the trip. Successfully doing so transitions ride to `IN_PROGRESS`.
- **Auth**: Bearer Token
- **Role Required**: `DRIVER` (assigned driver)
- **Request Body**:
  ```json
  {
    "otp": "4821"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "status": "IN_PROGRESS",
      "started_at": "2026-09-23T12:38:00Z"
    }
    ```
  - `400 Bad Request`: Incorrect OTP or ride not in `DRIVER_ARRIVED` status.

#### 11.2 `POST /rides/{ride_id}/share`
- **Purpose**: Generate a shareable ride tracking payload/link for emergency contacts.
- **Auth**: Bearer Token
- **Role Required**: `RIDER` (booked rider)
- **Responses**:
  - `200 OK`:
    ```json
    {
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "share_token": "sh_98a7sd8f7as6d8f",
      "tracking_url": "https://meterride.com/track/sh_98a7sd8f7as6d8f",
      "vehicle_details": {
        "model": "Hyundai Verna",
        "color": "White",
        "registration_number": "MH12AB1234"
      },
      "driver_name": "John Driver"
    }
    ```

#### 11.3 `POST /rides/{ride_id}/sos`
- **Purpose**: Trigger an immediate emergency SOS alert during a ride.
- **Auth**: Bearer Token
- **Role Required**: `RIDER` or `DRIVER`
- **Request Body**:
  ```json
  {
    "latitude": 18.530000,
    "longitude": 73.840000,
    "note": "Emergency assistance requested"
  }
  ```
- **Responses**:
  - `201 Created`:
    ```json
    {
      "incident_id": "d98e7f6a-5b4c-3a21-9876-fedcba098765",
      "ride_id": "7b687f6e-2139-4d2a-89cf-1e96a4a75412",
      "status": "OPEN",
      "alert_dispatched": true,
      "created_at": "2026-09-23T12:45:00Z"
    }
    ```

#### 11.4 `POST /rides/{ride_id}/incident`
- **Purpose**: Report a general safety incident or policy violation.
- **Auth**: Bearer Token
- **Role Required**: `RIDER` or `DRIVER`
- **Request Body**:
  ```json
  {
    "type": "RECKLESS_DRIVING",
    "description": "Driver was overspeeding and ignored red lights."
  }
  ```
- **Responses**:
  - `201 Created`: Returns created `SafetyIncident` object with status `OPEN`.

---

### Module 12: Admin & System Oversight

#### 12.1 `GET /admin/users`
- **Purpose**: List system users with filtering.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`
- **Query Parameters**: `role`, `is_active`, `limit`, `offset`
- **Responses**:
  - `200 OK`: Returns array of `User` objects.

#### 12.2 `GET /admin/drivers`
- **Purpose**: List all registered drivers and operational statuses.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`
- **Query Parameters**: `status`, `limit`, `offset`
- **Responses**:
  - `200 OK`: Returns array of `Driver` objects.

#### 12.3 `GET /admin/rides`
- **Purpose**: System-wide ride audit log.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`
- **Query Parameters**: `status`, `rider_id`, `driver_id`, `limit`, `offset`
- **Responses**:
  - `200 OK`: Returns array of `Ride` objects.

#### 12.4 `PATCH /admin/drivers/{driver_id}/approve`
- **Purpose**: Approve a driver's credentials and enable platform activation.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "is_approved": true,
      "status": "OFFLINE"
    }
    ```

#### 12.5 `PATCH /admin/drivers/{driver_id}/suspend`
- **Purpose**: Suspend driver privileges and force status to `OFFLINE`.
- **Auth**: Bearer Token
- **Role Required**: `ADMIN`
- **Responses**:
  - `200 OK`:
    ```json
    {
      "driver_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "status": "OFFLINE",
      "is_suspended": true
    }
    ```

---

## 7. Phase 01 Explicit Non-Goals

To maintain focus and guarantee delivery of a stable foundation, the following features are **strictly out of scope for Phase 01**:

1. **Real Payment Gateway**: No Razorpay/Stripe SDK integration; mock payment transaction states only.
2. **WebSocket Real-Time GPS Tracking**: No live socket streaming of driver coordinates; polling `/drivers/location` and `/drivers/nearby` is standard for Phase 01.
3. **External Push Notifications**: No Firebase Cloud Messaging (FCM) or Apple Push Notification service (APNs); notifications are database-persisted records queried via API.
4. **AI / ML Algorithms**: No machine learning models for driver matching, surge pricing, or demand heatmaps. Matching is distance/availability rule-based.
5. **Driver Location History / Telemetry Trails**: No breadcrumb GPS trails table; only current coordinates on `Driver` entity.
6. **Advanced Fraud / Anomaly Detection**: No automated facial recognition or biometric verification.
7. **Complex Admin Dashboards**: Admin endpoints are lightweight CRUD audit controls.

---

## 8. Developer Ownership & Module Allocation

To ensure parallel development across the 3 backend engineers without merge collisions:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TEAM BACKEND OWNERSHIP MATRIX                        │
├───────────────────────┬───────────────────────┬────────────────────────┤
│ Developer 1           │ Developer 2           │ Developer 3            │
│ (Ride Core)           │ (Identity & Fleet)    │ (Mobility Intelligence)│
├───────────────────────┼───────────────────────┼────────────────────────┤
│ • Fare Estimation     │ • Authentication      │ • Driver Location      │
│ • Ride Booking (CRUD) │ • Users Management    │ • Nearby Drivers API   │
│ • Ride Lifecycle & OTP│ • Driver Onboarding   │ • Driver Matching      │
│ • State Transitions   │ • Vehicle Fleet (CRUD)│ • Assignment & Retry   │
│ • Ride History        │ • Password & Tokens   │ • Proximity Filtering  │
└───────────────────────┴───────────────────────┴────────────────────────┘
```

### Secondary Module Assignments (Post-Core Integration):
- **Payments (Mock)**: Developer 1 (Ride Core)
- **Ratings & Safety**: Developer 2 (Identity & Fleet)
- **Notifications & Admin**: Developer 3 (Mobility Intelligence)

---

## 9. Contract Freeze Declaration

This document represents the **frozen API and schema specification** for Phase 01. No modifications may be made to request/response shapes, database schemas, or route signatures without formal team review.
