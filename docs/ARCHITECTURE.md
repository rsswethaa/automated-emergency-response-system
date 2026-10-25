# Architecture

```mermaid
flowchart LR
    S[Sensor-style input / User simulation] --> D[Severity Detector]
    D --> A[Flask Application]
    A --> I[(Incidents)]
    A --> L[(Alert Audit Log)]
    A --> R[Simulated Responder Notification]
    I --> B[Incident Dashboard]
    L --> B
```

## Severity logic
- **LOW:** impact below 2g
- **MEDIUM:** impact from 2g to below 4g
- **HIGH:** impact from 4g upward unless critical rule applies
- **CRITICAL:** impact at or above 6g combined with no detected movement after impact

The thresholds are illustrative portfolio logic only, not medically or automotive validated thresholds.

## Data model

```mermaid
erDiagram
    INCIDENTS ||--o{ ALERTS : generates
    INCIDENTS {
      int id PK
      float latitude
      float longitude
      float impact_g
      bool motion_after_impact
      string severity
      string status
      datetime created_at
    }
    ALERTS {
      int id PK
      int incident_id FK
      string recipient
      string channel
      string message
      datetime sent_at
    }
```

## Workflow
1. A simulated incident supplies location, impact and movement state.
2. `detector.py` assigns a severity category.
3. The incident is stored in SQLite.
4. A simulated notification is recorded in the alert audit table.
5. The dashboard displays incident state and allows resolution.
