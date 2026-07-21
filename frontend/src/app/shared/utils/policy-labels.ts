import { PolicyType } from '../../core/models';

export function policyTypeLabel(type: PolicyType): string {
  return type === 'car' ? 'Auto' : type === 'laptop' ? 'Laptop' : 'Paquete';
}

const STATUS_LABELS: Record<string, string> = {
  quote: 'Cotización',
  underwriting: 'Suscripción',
  in_force: 'Vigente',
  pending_cancel: 'En mora',
  cancelled: 'Cancelada',
  expired: 'Vencida',
  declined: 'Rechazada',
};

export function policyStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function policyStatusClass(status: string): string {
  switch (status) {
    case 'in_force':
      return 'bg-color4 text-color2';
    case 'pending_cancel':
      return 'bg-color3/30 text-color2';
    case 'quote':
    case 'underwriting':
      return 'bg-color3 text-color5';
    case 'cancelled':
    case 'declined':
      return 'bg-color2 text-color5';
    case 'expired':
    default:
      return 'bg-color5 text-color3';
  }
}

const EVENT_LABELS: Record<string, string> = {
  issued: 'Emitida',
  cancelled: 'Cancelada',
  endorsed: 'Endoso',
  renewed: 'Renovada',
  payment: 'Pago',
  claim_filed: 'Reclamo registrado',
};

export function policyEventLabel(eventType: string): string {
  return EVENT_LABELS[eventType] ?? eventType;
}

export function money(value: string | number): string {
  const n = Number(value);
  return Number.isFinite(n)
    ? n.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '0.00';
}
