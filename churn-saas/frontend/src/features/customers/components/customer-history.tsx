"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/features/auth/context/auth-context";
import { getCustomerHistory } from "../api/customers-api";
import { formatScore, zoneBadgeClass, zoneLabel } from "../risk";
import type { CustomerHistoryItem } from "../types";

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString("fr-FR", {
    dateStyle: "medium",
  });
}

function formatDelta(delta: number | null): string {
  if (delta === null) return "—";
  const points = Math.round(delta * 100);
  if (points === 0) return "0 point";
  return `${points > 0 ? "+" : ""}${points} point${Math.abs(points) > 1 ? "s" : ""}`;
}

const CHART_WIDTH = 640;
const CHART_HEIGHT = 180;
const PADDING = 28;

function ScoreCurve({ items }: { items: CustomerHistoryItem[] }) {
  const innerWidth = CHART_WIDTH - PADDING * 2;
  const innerHeight = CHART_HEIGHT - PADDING * 2;

  const points = items.map((item, index) => {
    const ratio = items.length === 1 ? 0.5 : index / (items.length - 1);
    return {
      x: PADDING + ratio * innerWidth,
      y: PADDING + (1 - item.score) * innerHeight,
      item,
    };
  });

  return (
    <svg
      viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
      role="img"
      aria-label="Évolution du score de risque dans le temps"
      className="h-auto w-full"
    >
      {[0, 0.5, 1].map((value) => {
        const y = PADDING + (1 - value) * innerHeight;
        return (
          <g key={value}>
            <line
              x1={PADDING}
              x2={CHART_WIDTH - PADDING}
              y1={y}
              y2={y}
              stroke="#dbeafe"
              strokeWidth={1}
            />
            <text x={4} y={y + 4} fontSize={10} fill="#1e3a8a">
              {Math.round(value * 100)} %
            </text>
          </g>
        );
      })}

      {points.length > 1 && (
        <polyline
          points={points.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke="#1d4ed8"
          strokeWidth={2.5}
        />
      )}

      {points.map((point) => (
        <circle
          key={point.item.prediction_id}
          cx={point.x}
          cy={point.y}
          r={4}
          fill="#1d4ed8"
        >
          <title>
            {formatDate(point.item.snapshot_date)} : {formatScore(point.item.score)}
          </title>
        </circle>
      ))}
    </svg>
  );
}

export function CustomerHistory({ customerId }: { customerId: number }) {
  const { token } = useAuth();

  const [items, setItems] = useState<CustomerHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    getCustomerHistory(token, customerId)
      .then((history) => {
        if (!cancelled) setItems(history.items);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Impossible de charger l’historique.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, customerId]);

  return (
    <section className="space-y-4 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-bold text-black">Historique du client</h2>
        <p className="mt-1 text-sm text-black">
          Évolution des scores calculés, de la plus ancienne à la plus récente
          observation.
        </p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-900">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-black">Chargement de l’historique…</p>
      ) : items.length === 0 ? (
        <p className="text-black">Aucune prédiction enregistrée.</p>
      ) : (
        <>
          <ScoreCurve items={items} />

          <div className="overflow-x-auto rounded-xl border border-blue-100">
            <table className="min-w-full divide-y divide-blue-100 text-left text-sm">
              <thead className="bg-blue-50 text-black">
                <tr>
                  <th className="px-4 py-3">Observation</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Zone</th>
                  <th className="px-4 py-3">Écart</th>
                  <th className="px-4 py-3">Modèle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-blue-100 text-black">
                {items.map((item) => (
                  <tr key={item.prediction_id}>
                    <td className="px-4 py-3">{formatDate(item.snapshot_date)}</td>
                    <td className="px-4 py-3 font-semibold">
                      {formatScore(item.score)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${zoneBadgeClass(
                          item.risk_level,
                        )}`}
                      >
                        {zoneLabel(item.risk_level)}
                      </span>
                    </td>
                    <td className="px-4 py-3">{formatDelta(item.delta)}</td>
                    <td className="px-4 py-3">{item.model_version || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
