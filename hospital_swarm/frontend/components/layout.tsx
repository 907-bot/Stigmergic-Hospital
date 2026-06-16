import Head from 'next/head';
import { useState } from 'react';
import LeftPanel from './left-panel';
import CenterPanel from './center-panel';
import RightPanel from './right-panel';
import BottomPanel from './bottom-panel';
import { useSimulationWS } from '@/hooks/useSimulationWS';

const containerStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '200px 1fr 200px',
  gridTemplateRows: '1fr 120px',
  gridTemplateAreas: `
    "left center right"
    "bottom bottom bottom"
  `,
  height: '100vh',
  width: '100vw',
  overflow: 'hidden',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif',
};

const panelBorder: React.CSSProperties = {
  border: '1px solid #e0e0e0',
  overflow: 'hidden',
};

const area: { [key: string]: React.CSSProperties } = {
  left: { ...panelBorder, gridArea: 'left' },
  center: { ...panelBorder, gridArea: 'center' },
  right: { ...panelBorder, gridArea: 'right' },
  bottom: { ...panelBorder, gridArea: 'bottom' },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const { data, connected } = useSimulationWS();
  const [simRunning, setSimRunning] = useState(false);

  const toggleSimulation = async () => {
    const action = simRunning ? 'stop' : 'start';
    try {
      const res = await fetch(`http://${window.location.hostname}:9001/api/v1/simulation/${action}`, { method: 'POST' });
      const result = await res.json();
      if (result.status === 'started' || result.status === 'stopped') {
        setSimRunning(!simRunning);
      }
    } catch (e) {
      console.error('Failed to toggle simulation', e);
    }
  };

  return (
    <>
      <Head>
        <title>Stigmergic Hospital Swarm OS</title>
        <meta name="description" content="Stigmergic Hospital Swarm OS Dashboard" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div style={containerStyle}>
        <div style={{
          position: 'fixed', top: 8, right: 8, zIndex: 100, display: 'flex', gap: 8, alignItems: 'center'
        }}>
          <span style={{
            width: 10, height: 10, borderRadius: '50%', background: connected ? '#4caf50' : '#f44336',
            display: 'inline-block'
          }} />
          <button
            onClick={toggleSimulation}
            style={{
              padding: '6px 16px', cursor: 'pointer', fontWeight: 600, fontSize: 13,
              background: simRunning ? '#f44336' : '#4caf50', color: '#fff', border: 'none', borderRadius: 4
            }}
          >
            {simRunning ? 'Stop Simulation' : 'Start Simulation'}
          </button>
        </div>
        <div style={area.left}><LeftPanel wsData={data} wsConnected={connected} /></div>
        <div style={area.center}><CenterPanel /></div>
        <div style={area.right}><RightPanel /></div>
        <div style={area.bottom}><BottomPanel wsData={data} /></div>
      </div>
    </>
  );
}