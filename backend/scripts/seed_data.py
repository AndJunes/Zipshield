"""Seed data matching the frontend mocks.

Centralizes the source-of-truth lists so seed.py just imports them.
"""
from datetime import datetime, timezone
from decimal import Decimal


SUPERVISORS = [
    {"id": 1, "full_name": "María Fernández", "status": "active", "contribution": "142500", "losses": "80000", "photo_url": "https://i.pravatar.cc/300?u=1", "created_at": "2026-06-22T08:15:00Z"},
    {"id": 2, "full_name": "Carlos Méndez", "status": "active", "contribution": "98300", "losses": "45000", "photo_url": "https://i.pravatar.cc/300?u=2", "created_at": "2026-06-22T11:40:00Z"},
    {"id": 3, "full_name": "Sofía Ramírez", "status": "inactive", "contribution": "54200", "losses": "30000", "photo_url": "https://i.pravatar.cc/300?u=3", "created_at": "2026-06-19T12:00:00Z"},
    {"id": 4, "full_name": "Diego Salazar", "status": "active", "contribution": "187900", "losses": "110000", "photo_url": "https://i.pravatar.cc/300?u=4", "created_at": "2026-06-16T09:00:00Z"},
    {"id": 5, "full_name": "Lucía Vargas", "status": "active", "contribution": "121650", "losses": "70000", "photo_url": "https://i.pravatar.cc/300?u=5", "created_at": "2026-06-10T11:00:00Z"},
    {"id": 6, "full_name": "Andrés Cabrera", "status": "inactive", "contribution": "43800", "losses": "50000", "photo_url": "https://i.pravatar.cc/300?u=6", "created_at": "2026-06-01T14:00:00Z"},
    {"id": 7, "full_name": "Valentina Ortiz", "status": "active", "contribution": "165400", "losses": "90000", "photo_url": "https://i.pravatar.cc/300?u=7", "created_at": "2026-05-15T14:00:00Z"},
    {"id": 8, "full_name": "Javier Rojas", "status": "active", "contribution": "89750", "losses": "40000", "photo_url": "https://i.pravatar.cc/300?u=8", "created_at": "2026-03-10T09:00:00Z"},
    {"id": 9, "full_name": "Camila Torres", "status": "active", "contribution": "203100", "losses": "95000", "photo_url": "https://i.pravatar.cc/300?u=9", "created_at": "2025-12-20T11:00:00Z"},
    {"id": 10, "full_name": "Tomás Herrera", "status": "inactive", "contribution": "31200", "losses": "35000", "photo_url": "https://i.pravatar.cc/300?u=10", "created_at": "2025-08-15T11:00:00Z"},
]


AGENTS = [
    {"id": 1, "full_name": "Mateo Aguirre", "status": "active", "contribution": "78400", "losses": "78000", "photo_url": "https://i.pravatar.cc/300?u=a1", "created_at": "2026-06-22T07:30:00Z", "supervisor_id": 1},
    {"id": 2, "full_name": "Renata Paredes", "status": "active", "contribution": "92100", "losses": "30000", "photo_url": "https://i.pravatar.cc/300?u=a2", "created_at": "2026-06-22T13:00:00Z", "supervisor_id": 2},
    {"id": 3, "full_name": "Bruno Lagos", "status": "inactive", "contribution": "24500", "losses": "0", "photo_url": "https://i.pravatar.cc/300?u=a3", "created_at": "2026-06-20T08:00:00Z", "supervisor_id": 3},
    {"id": 4, "full_name": "Florencia Núñez", "status": "active", "contribution": "134600", "losses": "55000", "photo_url": "https://i.pravatar.cc/300?u=a4", "created_at": "2026-06-17T10:30:00Z", "supervisor_id": 4},
    {"id": 5, "full_name": "Iván Espinoza", "status": "active", "contribution": "64900", "losses": "35000", "photo_url": "https://i.pravatar.cc/300?u=a5", "created_at": "2026-06-12T14:00:00Z", "supervisor_id": 5},
    {"id": 6, "full_name": "Paula Cisneros", "status": "inactive", "contribution": "18200", "losses": "23000", "photo_url": "https://i.pravatar.cc/300?u=a6", "created_at": "2026-06-02T11:00:00Z", "supervisor_id": 6},
    {"id": 7, "full_name": "Hugo Almeida", "status": "active", "contribution": "105300", "losses": "20000", "photo_url": "https://i.pravatar.cc/300?u=a7", "created_at": "2026-05-20T09:15:00Z", "supervisor_id": 7},
    {"id": 8, "full_name": "Sara Quiroga", "status": "active", "contribution": "47800", "losses": "13000", "photo_url": "https://i.pravatar.cc/300?u=a8", "created_at": "2026-04-08T16:00:00Z", "supervisor_id": 8},
    {"id": 9, "full_name": "Leandro Bustos", "status": "active", "contribution": "156900", "losses": "57000", "photo_url": "https://i.pravatar.cc/300?u=a9", "created_at": "2026-01-15T10:00:00Z", "supervisor_id": 9},
    {"id": 10, "full_name": "Antonella Ríos", "status": "active", "contribution": "88400", "losses": "23000", "photo_url": "https://i.pravatar.cc/300?u=a10", "created_at": "2025-11-22T13:00:00Z", "supervisor_id": 10},
    {"id": 11, "full_name": "Gonzalo Pereyra", "status": "inactive", "contribution": "12900", "losses": "0", "photo_url": "https://i.pravatar.cc/300?u=a11", "created_at": "2025-09-05T08:30:00Z", "supervisor_id": 1},
    {"id": 12, "full_name": "Daniela Cárdenas", "status": "active", "contribution": "71600", "losses": "16000", "photo_url": "https://i.pravatar.cc/300?u=a12", "created_at": "2025-07-10T11:00:00Z", "supervisor_id": 2},
]
