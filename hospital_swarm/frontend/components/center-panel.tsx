import { useSimulationWS } from '@/hooks/useSimulationWS';
import { useEffect, useState } from 'react';
import ReactFlow, { ReactFlowProvider, Background, Controls, MiniMap } from 'reactflow';
const { nodesToDraw, edgesToDraw } = ReactFlow;
import styles from '@/styles/center-panel.module.css';

// Types for our hospital graph
type HospitalNode = {
  id: string;
  type: 'input' | 'output' | 'default';
  position: { x: number; y: number };
  data: { label: string; type: string; status?: string };
  style?: { background: string; color: string };
};

type HospitalEdge = {
  id: string;
  source: string;
  target: string;
  type: 'smoothstep' | 'straight' | 'step';
  label?: string;
  animated?: boolean;
};

export default function CenterPanel() {
  const { data } = useSimulationWS();
  const [nodes, setNodes] = useState<HospitalNode[]>([]);
  const [edges, setEdges] = useState<HospitalEdge[]>([]);

  // Initialize some basic hospital elements
  useEffect(() => {
    // Create initial nodes representing hospital resources
    const initialNodes: HospitalNode[] = [
      {
        id: 'er',
        type: 'default',
        position: { x: 250, y: 50 },
        data: { label: 'ER', type: 'room', status: 'available' },
        style: { background: '#ffebee', color: '#c62828' }
      },
      {
        id: 'icu',
        type: 'default',
        position: { x: 250, y: 150 },
        data: { label: 'ICU', type: 'room', status: 'available' },
        style: { background: '#fff3e0', color: '#ef6c00' }
      },
      {
        id: 'ward_a',
        type: 'default',
        position: { x: 250, y: 250 },
        data: { label: 'Ward A', type: 'room', status: 'available' },
        style: { background: '#e8f5e8', color: '#2e7d32' }
      },
      {
        id: 'ward_b',
        type: 'default',
        position: { x: 250, y: 350 },
        data: { label: 'Ward B', type: 'room', status: 'available' },
        style: { background: '#e8f5e8', color: '#2e7d32' }
      },
      {
        id: 'lab',
        type: 'default',
        position: { x: 50, y: 200 },
        data: { label: 'Lab', type: 'facility', status: 'available' },
        style: { background: '#e3f2fd', color: '#1565c0' }
      },
      {
        id: 'pharmacy',
        type: 'default',
        position: { x: 450, y: 200 },
        data: { label: 'Pharmacy', type: 'facility', status: 'available' },
        style: { background: '#f3e5f5', color: '#6a1b9a' }
      }
    ];
    
    // Create initial edges (connections)
    const initialEdges: HospitalEdge[] = [
      { id: 'er-ward_a', source: 'er', target: 'ward_a', type: 'smoothstep', label: 'patient_flow' },
      { id: 'er-ward_b', source: 'er', target: 'ward_b', type: 'smoothstep', label: 'patient_flow' },
      { id: 'er-icu', source: 'er', target: 'icu', type: 'smoothstep', label: 'critical_transfer' },
      { id: 'ward_a-lab', source: 'ward_a', target: 'lab', type: 'smoothstep', label: 'lab_request' },
      { id: 'ward_b-lab', source: 'ward_b', target: 'lab', type: 'smoothstep', label: 'lab_request' },
      { id: 'icu-pharmacy', source: 'icu', target: 'pharmacy', type: 'smoothstep', label: 'medication' },
      { id: 'ward_a-pharmacy', source: 'ward_a', target: 'pharmacy', type: 'smoothstep', label: 'medication' },
      { id: 'ward_b-pharmacy', source: 'ward_b', target: 'pharmacy', type: 'smoothstep', label: 'medication' }
    ];
    
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, []);

  // Update nodes based on simulation data
  useEffect(() => {
    if (!data) return;
    
    // In a full implementation, we would update node colors/status based on simulation data
    // For example: update ER status based on patient count, etc.
    // This is a placeholder for that logic
  }, [data]);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Live Hospital Graph</h2>
        <div className={styles.controls}>
          <button className={styles.button} onClick={() => {
            // Reset to initial state
          }}>
            Reset View
          </button>
        </div>
      </div>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={{
            default: (_: any) => {
              const { data, id, position, selected, sourcePosition, targetPosition, style } = _;
              return (
                <div 
                  className="node"
                  style={{
                    background: data.style?.background || '#fff',
                    color: data.style?.color || '#000',
                    border: selected ? '2px solid #ff9800' : '1px solid #ddd',
                    borderRadius: '4px',
                    padding: '8px',
                    textAlign: 'center',
                    width: '80px',
                    position: 'absolute',
                    left: `${position.x}px`,
                    top: `${position.y}px`,
                    ...(style || {})
                  }}
                >
                  <div>{data.label}</div>
                  {data.status && <div className="status">{data.status}</div>}
                </div>
              );
            }
          }}
          elementsToDraw={{
            nodes: nodesToDraw,
            edges: edgesToDraw
          }}
          zoomable
          panOnDrag
          fitView
          showGrid
          nodesDraggable
          style={{ width: '100%', height: '100%', position: 'relative' }}
        >
          <Background />
          <Controls />
          <MiniMap nodeColor={(node: any) => node.data?.color || '#ff9800'} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}