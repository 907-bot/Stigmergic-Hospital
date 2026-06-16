import { useSimulationWS } from '@/hooks/useSimulationWS';
import { useEffect, useState, useCallback } from 'react';
import ReactFlow, { ReactFlowProvider, Background, Controls, MiniMap, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

type HospitalNode = Node & {
  data: { label: string; type: string; status?: string };
};

type HospitalEdge = Edge & {
  type: 'smoothstep' | 'straight' | 'step';
  label?: string;
  animated?: boolean;
};

const CustomNode = ({ data }: { data: { label: string; status?: string; color?: string; background?: string } }) => (
  <div
    style={{
      background: data.background || '#fff',
      color: data.color || '#000',
      border: '1px solid #ddd',
      borderRadius: '4px',
      padding: '8px',
      textAlign: 'center',
      width: 80,
      fontSize: 12,
    }}
  >
    <div>{data.label}</div>
    {data.status && <div style={{ marginTop: 4, fontSize: 10, opacity: 0.7 }}>{data.status}</div>}
  </div>
);

const nodeTypes = { default: CustomNode };

export default function CenterPanel() {
  const { data } = useSimulationWS();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    const initialNodes: Node[] = [
      { id: 'er', type: 'default', position: { x: 250, y: 50 }, data: { label: 'ER', type: 'room', status: 'available', background: '#ffebee', color: '#c62828' } },
      { id: 'icu', type: 'default', position: { x: 250, y: 150 }, data: { label: 'ICU', type: 'room', status: 'available', background: '#fff3e0', color: '#ef6c00' } },
      { id: 'ward_a', type: 'default', position: { x: 250, y: 250 }, data: { label: 'Ward A', type: 'room', status: 'available', background: '#e8f5e8', color: '#2e7d32' } },
      { id: 'ward_b', type: 'default', position: { x: 250, y: 350 }, data: { label: 'Ward B', type: 'room', status: 'available', background: '#e8f5e8', color: '#2e7d32' } },
      { id: 'lab', type: 'default', position: { x: 50, y: 200 }, data: { label: 'Lab', type: 'facility', status: 'available', background: '#e3f2fd', color: '#1565c0' } },
      { id: 'pharmacy', type: 'default', position: { x: 450, y: 200 }, data: { label: 'Pharmacy', type: 'facility', status: 'available', background: '#f3e5f5', color: '#6a1b9a' } },
    ];
    const initialEdges: Edge[] = [
      { id: 'er-ward_a', source: 'er', target: 'ward_a', type: 'smoothstep', label: 'patient_flow' },
      { id: 'er-ward_b', source: 'er', target: 'ward_b', type: 'smoothstep', label: 'patient_flow' },
      { id: 'er-icu', source: 'er', target: 'icu', type: 'smoothstep', label: 'critical_transfer' },
      { id: 'ward_a-lab', source: 'ward_a', target: 'lab', type: 'smoothstep', label: 'lab_request' },
      { id: 'ward_b-lab', source: 'ward_b', target: 'lab', type: 'smoothstep', label: 'lab_request' },
      { id: 'icu-pharmacy', source: 'icu', target: 'pharmacy', type: 'smoothstep', label: 'medication' },
      { id: 'ward_a-pharmacy', source: 'ward_a', target: 'pharmacy', type: 'smoothstep', label: 'medication' },
      { id: 'ward_b-pharmacy', source: 'ward_b', target: 'pharmacy', type: 'smoothstep', label: 'medication' },
    ];
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, []);

  useEffect(() => {
    if (!data) return;
  }, [data]);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Live Hospital Graph</h2>
        <button
          onClick={() => {
            // Reset view
          }}
          style={{ padding: '4px 12px', cursor: 'pointer' }}
        >
          Reset View
        </button>
      </div>
      <div style={{ flex: 1 }}>
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            style={{ width: '100%', height: '100%' }}
          >
            <Background />
            <Controls />
            <MiniMap nodeColor={(node: any) => node.data?.color || '#999'} />
          </ReactFlow>
        </ReactFlowProvider>
      </div>
    </div>
  );
}