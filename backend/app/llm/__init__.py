"""Módulo LLM de Zipshield: análisis automático de claims con OpenRouter (modelo con visión).

Punto de entrada público:
    from app.llm.service import analyze_claim
    fields = analyze_claim(db, claim)   # dict con los 10 campos listos para guardar

El "cerebro" (prompts, validación de salida y capa anti-inyección) está portado del reto
de HackerRank casi sin cambios; la cáscara de entrada/salida se adaptó al backend de Zipshield.
"""
