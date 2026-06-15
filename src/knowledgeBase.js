const programs = require('../data/programs.json');

function matchPrograms(profile) {
  const { age, department, familySituation, canPay, icfesScore } = profile;
  const dept = department?.toLowerCase().replace(/á/g, 'a').replace(/é/g, 'e');
  const score = parseInt(icfesScore) || 0;
  const isBoyaca = dept?.includes('boyac');
  const isLowIncome = canPay === 'no' || canPay === 'partial';

  return programs.filter((p) => {
    const reqs = p.requisitos;

    if (reqs.icfes_minimo && score > 0 && score < reqs.icfes_minimo) return false;
    if (reqs.edad_minima && age < reqs.edad_minima) return false;
    if (reqs.edad_maxima && age > reqs.edad_maxima) return false;

    if (reqs.departamentos && !reqs.departamentos.includes('todos')) {
      if (!isBoyaca && reqs.departamentos.includes('boyaca') && reqs.departamentos.length === 1) return false;
    }

    if (p.id === 'caja_compensacion' && familySituation !== 'empleado_formal') return false;
    if (p.id === 'beca_bicentenario' && score < 370) return false;
    if (p.id === 'generacion_e_excelencia' && score < 310) return false;

    return true;
  });
}

function buildKnowledgeContext(profile, matches) {
  const lines = [`PERFIL DEL ESTUDIANTE:`];
  if (profile.age) lines.push(`- Edad: ${profile.age} años`);
  if (profile.department) lines.push(`- Departamento: ${profile.department}`);
  if (profile.familySituation) lines.push(`- Situación familiar: ${profile.familySituation}`);
  if (profile.canPay) lines.push(`- Puede pagar universidad: ${profile.canPay}`);
  if (profile.icfesScore) lines.push(`- Puntaje ICFES: ${profile.icfesScore}`);

  lines.push(`\nPROGRAMAS RELEVANTES ENCONTRADOS (${matches.length}):`);
  matches.forEach((p, i) => {
    lines.push(`\n${i + 1}. ${p.nombre} [${p.entidad}]`);
    lines.push(`   Tipo: ${p.tipo} | Costo: ${p.costo}`);
    lines.push(`   Descripción: ${p.descripcion}`);
    lines.push(`   Documentos: ${p.documentos.join(', ')}`);
    lines.push(`   Pasos: ${p.pasos.map((s, n) => `${n + 1}) ${s}`).join(' | ')}`);
    lines.push(`   Contacto: ${p.contacto}`);
  });

  return lines.join('\n');
}

module.exports = { matchPrograms, buildKnowledgeContext };
