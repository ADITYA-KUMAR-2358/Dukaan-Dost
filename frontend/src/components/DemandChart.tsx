import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartKey } from "./ChartKey";
import { ChartTip } from "./ChartTip";

export type DemandPoint = {
  label: string;
  sold: number | null;
  forecast: number | null;
};

export function DemandChart({
  points,
  summary,
  illustrative = false,
  animate = true,
  quiet = false,
}: {
  points: DemandPoint[];
  summary: string;
  illustrative?: boolean;
  animate?: boolean;
  quiet?: boolean;
}) {
  const [asTable, setAsTable] = useState(false);

  return (
    <div className={illustrative ? "illustrative" : undefined}>
      {illustrative && !quiet ? (
        <span className="prov-tag" title="Seasonal demonstration. Not a model result and not your shop.">
          Illustrative
        </span>
      ) : null}
      <p className={quiet ? "sr-only" : "mt-2 text-sm"}>{summary}</p>
      {asTable ? (
        <table className="mt-3 w-full text-sm">
          <caption className="sr-only">Forecast figures</caption>
          <thead>
            <tr className="text-left text-[var(--muted)]">
              <th className="py-1 font-medium">Day</th>
              <th className="py-1 text-right font-medium">Sold</th>
              <th className="py-1 text-right font-medium">Forecast</th>
            </tr>
          </thead>
          <tbody>
            {points.map((point) => (
              <tr key={point.label}>
                <th className="py-1 text-left font-medium" scope="row">{point.label}</th>
                <td className="nums py-1 text-right">{point.sold ?? ""}</td>
                <td className="nums py-1 text-right">{point.forecast ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className={quiet ? "h-44" : "mt-3 h-40"}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points}>
              <CartesianGrid stroke="var(--line)" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
              <YAxis width={28} tick={{ fill: "var(--muted)", fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTip />} />
              <Line type="monotone" dataKey="sold" name="Sold" stroke="var(--series-actual)" strokeWidth={2} dot={false} isAnimationActive={animate} />
              <Line type="monotone" dataKey="forecast" name="Forecast" stroke="var(--series-forecast)" strokeWidth={2} strokeDasharray="6 4" dot={false} connectNulls={false} isAnimationActive={animate} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <ChartKey
        className="mt-2"
        items={[
          { kind: "solid", label: "Sold" },
          { kind: "dashed", label: "Forecast" },
          ...(quiet ? [{ kind: "dot" as const, label: "Order by" }] : []),
        ]}
      />
      {quiet ? null : (
        <>
          <button type="button" className="btn btn-quiet mt-3" onClick={() => setAsTable((value) => !value)}>
            {asTable ? "View as chart" : "View as table"}
          </button>
        </>
      )}
    </div>
  );
}
