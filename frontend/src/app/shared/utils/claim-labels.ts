const RISK_FLAGS: Record<string, string> = {
  none: 'Sin observaciones',
  damage_not_visible: 'Daño no visible',
  user_history_risk: 'Riesgo por historial',
  claim_mismatch: 'Reclamo no coincide',
  wrong_object_part: 'Parte incorrecta del objeto',
  blurry_image: 'Imagen borrosa',
  text_instruction_present: 'Instrucción en texto',
  manual_review_required: 'Requiere revisión manual',
  low_light_or_glare: 'Poca luz o reflejos',
  non_original_image: 'Imagen no original',
  wrong_object: 'Objeto incorrecto',
};

const ISSUE_TYPES: Record<string, string> = {
  scratch: 'Rayón',
  dent: 'Abolladura',
  glass_shatter: 'Vidrio quebrado',
  crack: 'Fisura',
  missing_part: 'Parte faltante',
  broken_part: 'Parte rota',
  stain: 'Mancha',
  water_damage: 'Daño por agua',
  crushed_packaging: 'Embalaje aplastado',
  unknown: 'Desconocido',
  none: 'Ninguno',
};

const OBJECT_PARTS: Record<string, string> = {
  front_bumper: 'Paragolpes delantero',
  door: 'Puerta',
  windshield: 'Parabrisas',
  side_mirror: 'Espejo lateral',
  hood: 'Capó',
  rear_bumper: 'Paragolpes trasero',
  headlight: 'Faro',
  screen: 'Pantalla',
  keyboard: 'Teclado',
  trackpad: 'Trackpad',
  hinge: 'Bisagra',
  package_corner: 'Esquina del paquete',
  seal: 'Sello',
  box: 'Caja',
  contents: 'Contenido',
  label: 'Etiqueta',
  lid: 'Tapa',
  corner: 'Esquina',
  unknown: 'Desconocida',
};

const SEVERITY: Record<string, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
  unknown: 'Desconocida',
  none: 'Ninguna',
};

function humanize(value: string): string {
  if (!value) return '';
  const spaced = value.replace(/_/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function formatRiskFlag(flag: string): string {
  return RISK_FLAGS[flag] ?? humanize(flag);
}

export function formatIssueType(value: string): string {
  return ISSUE_TYPES[value] ?? humanize(value);
}

export function formatObjectPart(value: string): string {
  return OBJECT_PARTS[value] ?? humanize(value);
}

export function formatSeverity(value: string): string {
  return SEVERITY[value] ?? humanize(value);
}
