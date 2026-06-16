const s: { [key: string]: React.CSSProperties } = {
  panel: { height: '100%', display: 'flex', flexDirection: 'column', padding: 8 },
  title: { margin: 0, marginBottom: 8, fontSize: 14, fontWeight: 600 },
  metrics: { display: 'flex', gap: 24, flexWrap: 'wrap' },
  metric: { display: 'flex', flexDirection: 'column', alignItems: 'center' },
  metricLabel: { fontSize: 11, opacity: 0.7 },
  metricValue: { fontSize: 18, fontWeight: 700 },
};

export default function BottomPanel({ wsData }: { wsData: any }) {
  const patientsGenerated = wsData?.simulation?.stats?.patients_generated || 0;
  const agentsActions = wsData?.simulation?.stats?.agents_actions || 0;

  return (
    <div style={s.panel}>
      <h2 style={s.title}>Metrics</h2>
      <div style={s.metrics}>
        <div style={s.metric}>
          <span style={s.metricValue}>45ms</span>
          <span style={s.metricLabel}>Avg Wait Time</span>
        </div>
        <div style={s.metric}>
          <span style={s.metricValue}>65%</span>
          <span style={s.metricLabel}>Resource Utilization</span>
        </div>
        <div style={s.metric}>
          <span style={s.metricValue}>95%</span>
          <span style={s.metricLabel}>Signal Delivery Rate</span>
        </div>
        <div style={s.metric}>
          <span style={s.metricValue}>{patientsGenerated}</span>
          <span style={s.metricLabel}>Patients</span>
        </div>
        <div style={s.metric}>
          <span style={s.metricValue}>{agentsActions}</span>
          <span style={s.metricLabel}>Agent Actions</span>
        </div>
      </div>
    </div>
  );
}