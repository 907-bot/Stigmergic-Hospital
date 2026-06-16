const s: { [key: string]: React.CSSProperties } = {
  panel: { height: '100%', display: 'flex', flexDirection: 'column', padding: 16, overflow: 'auto' },
  title: { margin: 0, marginBottom: 16, fontSize: 16, fontWeight: 600 },
  resources: { display: 'flex', flexDirection: 'column', gap: 8 },
  resourceItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontWeight: 500 },
  value: { opacity: 0.8 },
  statsSection: { marginTop: 24, borderTop: '1px solid #eee', paddingTop: 16 },
  statsTitle: { margin: 0, marginBottom: 8, fontSize: 14, fontWeight: 600 },
  statsItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  statsLabel: { fontSize: 12 },
  statsValue: { fontSize: 12, fontWeight: 600 },
};

export default function LeftPanel({ wsData, wsConnected }: { wsData: any; wsConnected: boolean }) {
  const patientsGenerated = wsData?.simulation?.stats?.patients_generated || 0;
  const pheromonesCreated = wsData?.simulation?.stats?.pheromones_created || 0;
  const agentsActions = wsData?.simulation?.stats?.agents_actions || 0;

  return (
    <div style={s.panel}>
      <h2 style={s.title}>Hospital Resources</h2>
      <div style={s.resources}>
        <div style={s.resourceItem}><span style={s.label}>ER:</span><span style={s.value}>Available</span></div>
        <div style={s.resourceItem}><span style={s.label}>ICU:</span><span style={s.value}>Available</span></div>
        <div style={s.resourceItem}><span style={s.label}>Ward A:</span><span style={s.value}>Available</span></div>
        <div style={s.resourceItem}><span style={s.label}>Ward B:</span><span style={s.value}>Available</span></div>
        <div style={s.resourceItem}><span style={s.label}>Lab:</span><span style={s.value}>Available</span></div>
        <div style={s.resourceItem}><span style={s.label}>Pharmacy:</span><span style={s.value}>Available</span></div>
      </div>
      
      <div style={s.statsSection}>
        <h3 style={s.statsTitle}>Simulation Stats</h3>
        <div style={s.statsItem}><span style={s.statsLabel}>Patients Generated:</span><span style={s.statsValue}>{patientsGenerated}</span></div>
        <div style={s.statsItem}><span style={s.statsLabel}>Pheromones Created:</span><span style={s.statsValue}>{pheromonesCreated}</span></div>
        <div style={s.statsItem}><span style={s.statsLabel}>Agent Actions:</span><span style={s.statsValue}>{agentsActions}</span></div>
      </div>
    </div>
  );
}