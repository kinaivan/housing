import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

// Theme colors
const colors = {
  yellowPrimary: '#FFD700', // Golden yellow
  yellowLight: '#FFF4B8',   // Light yellow
  yellowDark: '#FFC000',    // Dark yellow
  textDark: '#2C2C2C',     // Dark text
  gridColor: '#FFE5B4',    // Peach yellow for grid
  background: '#FFFDF0',   // Very light yellow background
  occupiedLine: '#28a745',  // Green for occupied units
  rentLine: '#dc3545',     // Red for rent
  unhousedLine: '#6c757d', // Gray for unhoused
};

type Frame = {
  year?: number;
  period?: number;
  unhoused?: number;
  metrics?: {
    occupied_units?: number;
    total_units?: number;
    average_rent?: number;
    median_rent?: number;
    occupancy_rate?: number;
    [key: string]: number | undefined;
  };
};

interface Props {
  frame: Frame | null;
}

const SimulationGraph: React.FC<Props> = ({ frame }) => {
  const [history, setHistory] = useState<Frame[]>([]);

  // Update history when new frame arrives
  useEffect(() => {
    if (frame) {
      setHistory(prev => [...prev, frame]);
    }
  }, [frame]);

  // Prepare data series
  const data = [
    {
      x: history.map(f => f.period),
      y: history.map(f => f.metrics?.occupied_units || 0),
      name: 'Occupied Units',
      mode: 'lines+markers',
      line: { 
        color: colors.occupiedLine,
        width: 3,
      },
      marker: {
        color: colors.occupiedLine,
        size: 8,
      },
    },
    {
      x: history.map(f => f.period),
      y: history.map(f => f.metrics?.average_rent || 0),
      name: 'Average Rent',
      mode: 'lines+markers',
      yaxis: 'y2',
      line: { 
        color: colors.rentLine,
        width: 3,
      },
      marker: {
        color: colors.rentLine,
        size: 8,
      },
    },
    {
      x: history.map(f => f.period),
      y: history.map(f => f.unhoused || 0),
      name: 'Unhoused',
      mode: 'lines+markers',
      yaxis: 'y3',
      line: { 
        color: colors.unhousedLine,
        width: 3,
      },
      marker: {
        color: colors.unhousedLine,
        size: 8,
      },
    },
  ];

  return (
    <Plot
      data={data}
      layout={{
        title: {
          text: 'Market Dynamics Over Time',
          font: { 
            color: colors.textDark,
            size: 24,
          },
          x: 0.5,
          xanchor: 'center',
          y: 0.95,
          yanchor: 'top',
        },
        paper_bgcolor: colors.background,
        plot_bgcolor: colors.background,
        xaxis: {
          title: {
            text: 'Period',
            font: { color: colors.textDark, size: 14 }
          },
          gridcolor: colors.gridColor,
          zerolinecolor: colors.yellowDark,
          tickfont: { color: colors.textDark, size: 12 },
          showgrid: true,
          zeroline: true,
          range: [-1, Math.max(10, ...history.map(f => f.period || 0))],
        },
        yaxis: {
          title: {
            text: 'Occupied Units',
            font: { color: colors.occupiedLine, size: 14 }
          },
          gridcolor: colors.gridColor,
          zerolinecolor: colors.yellowDark,
          tickfont: { color: colors.textDark, size: 12 },
          showgrid: true,
          zeroline: true,
          range: [0, Math.max(100, ...history.map(f => f.metrics?.occupied_units || 0) as number[])],
        },
        yaxis2: {
          title: {
            text: 'Average Rent ($)',
            font: { color: colors.rentLine, size: 14 }
          },
          overlaying: 'y',
          side: 'right',
          tickfont: { color: colors.textDark, size: 12 },
          showgrid: false,
          range: [0, Math.max(2000, ...history.map(f => f.metrics?.average_rent || 0) as number[])],
        },
        yaxis3: {
          title: {
            text: 'Unhoused',
            font: { color: colors.unhousedLine, size: 14 }
          },
          overlaying: 'y',
          side: 'left',
          position: 0.05,
          tickfont: { color: colors.textDark, size: 12 },
          showgrid: false,
          range: [0, Math.max(10, ...history.map(f => f.unhoused || 0))],
        },
        showlegend: true,
        legend: {
          x: 0.5,
          y: 1.2,
          xanchor: 'center',
          yanchor: 'top',
          orientation: 'h',
          bgcolor: colors.background,
          bordercolor: colors.yellowPrimary,
          borderwidth: 1,
          font: { color: colors.textDark, size: 12 },
        },
        margin: { t: 100, r: 70, l: 70, b: 50 },
        modebar: {
          bgcolor: colors.yellowLight,
          color: colors.yellowDark,
          activecolor: colors.yellowPrimary,
        },
        autosize: true,
        height: 550,
      }}
      style={{ 
        width: '100%', 
        height: '100%',
        minHeight: '500px' 
      }}
      useResizeHandler={true}
      config={{
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: [
          'lasso2d',
          'select2d',
          'autoScale2d',
        ],
        toImageButtonOptions: {
          format: 'png',
          filename: 'housing_market_simulation',
          height: 800,
          width: 1200,
          scale: 2,
        },
      }}
    />
  );
};

export default SimulationGraph; 