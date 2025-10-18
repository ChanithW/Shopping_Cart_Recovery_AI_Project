# Cart Abandonment Detection System - Technical Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask E-Commerce App                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Cart Abandonment Detector                   │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  CartAbandonmentDetector (Main Controller)      │  │  │
│  │  │  - Monitors cart table every 30 seconds         │  │  │
│  │  │  - Identifies inactive carts (1+ min)           │  │  │
│  │  │  - Triggers recovery workflow                   │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                          │                             │  │
│  │           ┌──────────────┼──────────────┐              │  │
│  │           ▼              ▼              ▼              │  │
│  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐   │  │
│  │  │ Email       │ │ Recommend.   │ │ Database     │   │  │
│  │  │ Service     │ │ Engine       │ │ Connection   │   │  │
│  │  └─────────────┘ └──────────────┘ └──────────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  MySQL   │     │  Gemini  │     │   SMTP   │
  │ Database │     │   API    │     │  Server  │
  └──────────┘     └──────────┘     └──────────┘
```

