export type DemoProduct = {
  id: string;
  name: string;
  note: string;
  history: number[];
};

export const DEMO_PRODUCTS: DemoProduct[] = [
  {
    id: "diya",
    name: "Clay diya set",
    note: "12 pieces. Festival window in this sample.",
    history: [2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 8, 9, 9],
  },
  {
    id: "notebook",
    name: "Classmate notebook",
    note: "172 pages. School term.",
    history: [5, 5, 5, 5, 5, 7, 7, 5, 5, 5, 5, 5, 7, 7, 5, 5, 5, 5, 5, 7, 7, 5, 5, 5, 5, 5, 7, 7],
  },
  {
    id: "ors",
    name: "ORS sachet, orange",
    note: "Medical. Peaks on some days.",
    history: [0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0],
  },
  {
    id: "parle",
    name: "Parle-G 200g",
    note: "Steady. Shops order weekly.",
    history: [4, 4, 4, 4, 5, 6, 6, 4, 4, 4, 4, 5, 6, 6, 4, 4, 4, 4, 5, 6, 6, 4, 4, 4, 4, 5, 6, 6],
  },
];

export function seasonalForecast(history: number[], horizon: number): number[] {
  const season = 7;
  const values: number[] = [];
  for (let step = 1; step <= horizon; step += 1) {
    let index = history.length - season + (step - 1);
    while (index >= history.length) index -= season;
    values.push(Math.max(0, history[index] ?? 0));
  }
  return values;
}

export function demoAdvice(history: number[], horizon: number) {
  const forecast = seasonalForecast(history, horizon);
  const total = forecast.reduce((sum, value) => sum + value, 0);
  const recent = history.slice(-7).reduce((sum, value) => sum + value, 0);
  return {
    forecast,
    total: Math.round(total),
    recent,
    suggestion: total > recent ? "Plan a refill before the weekend rush." : "Current pace is calm. Check the shelf before ordering more.",
  };
}
