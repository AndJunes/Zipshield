import { formatIssueType, formatObjectPart, formatRiskFlag } from './claim-labels';

describe('claim-labels — A13: cobertura completa de valores que el backend puede devolver', () => {
  it('traduce los risk_flags que antes faltaban', () => {
    expect(formatRiskFlag('cropped_or_obstructed')).toBe('Recortada u obstruida');
    expect(formatRiskFlag('wrong_angle')).toBe('Ángulo incorrecto');
    expect(formatRiskFlag('possible_manipulation')).toBe('Posible manipulación');
  });

  it('traduce el issue_type que antes faltaba', () => {
    expect(formatIssueType('torn_packaging')).toBe('Embalaje rasgado');
  });

  it('traduce los object_part de car que antes faltaban', () => {
    expect(formatObjectPart('taillight')).toBe('Luz trasera');
    expect(formatObjectPart('fender')).toBe('Guardabarros');
    expect(formatObjectPart('quarter_panel')).toBe('Panel trasero lateral');
  });

  it('traduce los object_part de laptop y package que antes faltaban', () => {
    expect(formatObjectPart('port')).toBe('Puerto');
    expect(formatObjectPart('package_side')).toBe('Costado del paquete');
    expect(formatObjectPart('item')).toBe('Artículo');
  });

  it('el fallback mecánico solo se usa para valores realmente no mapeados', () => {
    expect(formatObjectPart('valor_inventado')).toBe('Valor inventado');
  });
});
