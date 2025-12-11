import React from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import { RiskChartData } from '../types';

ChartJS.register(ArcElement, Tooltip, Legend);

interface RiskChartProps {
  data: RiskChartData;
}

const RiskChart: React.FC<RiskChartProps> = ({ data }) => {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        data: data.values,
        backgroundColor: data.colors,
        borderColor: '#0f172a',
      },
    ],
  };

  const options = {
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#e5e7eb',
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${ctx.label}: ${ctx.formattedValue}%`,
        },
      },
    },
  };

  return (
    <div className="w-full">
      <p className="mb-2 text-sm font-semibold text-gray-100">Распределение рисков</p>
      <Pie data={chartData} options={options} />
    </div>
  );
};

export default RiskChart;

