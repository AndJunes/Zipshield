import { formatIssueType, formatObjectPart, formatRiskFlag } from './claim-labels';

describe('claim-labels — full coverage of values the backend can return', () => {
  it('maps every risk_flag to a label', () => {
    expect(formatRiskFlag('cropped_or_obstructed')).toBe('Recortada u obstruida');
    expect(formatRiskFlag('wrong_angle')).toBe('Ángulo incorrecto');
    expect(formatRiskFlag('possible_manipulation')).toBe('Posible manipulación');
  });

  it('maps torn_packaging to its issue_type label', () => {
    expect(formatIssueType('torn_packaging')).toBe('Embalaje rasgado');
  });

  it('maps the car object_part values', () => {
    expect(formatObjectPart('taillight')).toBe('Luz trasera');
    expect(formatObjectPart('fender')).toBe('Guardabarros');
    expect(formatObjectPart('quarter_panel')).toBe('Panel trasero lateral');
  });

  it('maps the laptop and package object_part values', () => {
    expect(formatObjectPart('port')).toBe('Puerto');
    expect(formatObjectPart('package_side')).toBe('Costado del paquete');
    expect(formatObjectPart('item')).toBe('Artículo');
  });

  it('uses the mechanical fallback only for truly unmapped values', () => {
    expect(formatObjectPart('valor_inventado')).toBe('Valor inventado');
  });
});
