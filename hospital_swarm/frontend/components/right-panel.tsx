import { useSimulationWS } from '@/hooks/useSimulationWS';

const s: { [key: string]: React.CSSProperties } = {
  panel: { height: '100%', display: 'flex', flexDirection: 'column', padding: 16 },
  title: { margin: 0, marginBottom: 16, fontSize: 16, fontWeight: 600 },
  streams: { display: 'flex', flexDirection: 'column', gap: 8 },
  streamItem: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontWeight: 500 },
  value: { opacity: 0.8 },
};

export default function RightPanel() {
  const { data } = useSimulationWS();
  
  const pheromoneStreams = [
    { type: 'EMERGENCY', strength: 0.8, active: true },
    { type: 'ICU', strength: 0.6, active: true },
    { type: 'SURGERY', strength: 0.3, active: false },
    { type: 'LAB', strength: 0.5, active: true },
    { type: 'PHARMACY', strength: 0.7, active: true },
  ];

  return (
    <div style={s.panel}>
      <h2 style={s.title}>Pheromone Streams</h2>
      <div style={s.streams}>
        {pheromoneStreams.map((stream, i) => (
          <div key={i} style={s.streamItem}>
            <span style={s.label}>{stream.type}:</span>
            <span style={s.value}>
              {stream.active ? 'Active' : 'Inactive'}
              {stream.active && stream.strength ? ` (${(stream.strength * 100).toFixed(0)}%)` : ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}