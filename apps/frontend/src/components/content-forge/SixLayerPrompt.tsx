import { useState } from "react";
import {
  Monitor,
  LayoutTemplate,
  BookOpen,
  KeyRound,
  UserCircle,
  Palette,
  ChevronDown,
  ChevronUp,
  Layers,
} from "lucide-react";

export interface PromptLayer {
  key: string;
  label: string;
  description: string;
  content: string;
}

interface SixLayerPromptProps {
  layers: PromptLayer[];
  isLoading?: boolean;
}

const LAYER_ICONS: Record<string, React.ElementType> = {
  platform_format: Monitor,
  structure_template: LayoutTemplate,
  brand_knowledge: BookOpen,
  keyword_injection: KeyRound,
  persona_layer: UserCircle,
  style_layer: Palette,
};

const LAYER_COLORS: Record<string, string> = {
  platform_format: "text-blue-600 bg-blue-50 border-blue-200",
  structure_template: "text-emerald-600 bg-emerald-50 border-emerald-200",
  brand_knowledge: "text-amber-600 bg-amber-50 border-amber-200",
  keyword_injection: "text-rose-600 bg-rose-50 border-rose-200",
  persona_layer: "text-violet-600 bg-violet-50 border-violet-200",
  style_layer: "text-cyan-600 bg-cyan-50 border-cyan-200",
};

const LAYER_BAR_COLORS: Record<string, string> = {
  platform_format: "bg-blue-500",
  structure_template: "bg-emerald-500",
  brand_knowledge: "bg-amber-500",
  keyword_injection: "bg-rose-500",
  persona_layer: "bg-violet-500",
  style_layer: "bg-cyan-500",
};

export function SixLayerPrompt({ layers, isLoading }: SixLayerPromptProps) {
  const [expanded, setExpanded] = useState<Set<string>>(
    new Set(layers.map((l) => l.key))
  );

  const toggleLayer = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 space-y-3 animate-pulse">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-5 h-5 rounded bg-muted" />
          <div className="h-4 w-32 rounded bg-muted" />
        </div>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-10 rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (!layers || layers.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center text-muted-foreground text-sm">
        暂无 Prompt 分解数据
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <Layers className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-semibold text-foreground">
          六层 Prompt 透视
        </h3>
        <span className="text-[10px] text-muted-foreground ml-auto">
          {layers.length} 层
        </span>
      </div>

      {/* Layers */}
      <div className="divide-y divide-border">
        {layers.map((layer, index) => {
          const Icon = LAYER_ICONS[layer.key] || Layers;
          const isOpen = expanded.has(layer.key);
          const colorClass = LAYER_COLORS[layer.key] || "text-gray-600 bg-gray-50 border-gray-200";
          const barColor = LAYER_BAR_COLORS[layer.key] || "bg-gray-400";

          return (
            <div key={layer.key} className="group">
              {/* Layer header */}
              <button
                onClick={() => toggleLayer(layer.key)}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50 transition-colors text-left"
              >
                {/* Layer number bar */}
                <div className="flex flex-col items-center gap-0.5">
                  <div className={`w-1 h-6 rounded-full ${barColor}`} />
                  <span className="text-[10px] font-bold text-muted-foreground">
                    L{index + 1}
                  </span>
                </div>

                {/* Icon */}
                <div
                  className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${colorClass}`}
                >
                  <Icon className="w-3.5 h-3.5" />
                </div>

                {/* Label & desc */}
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-foreground">
                    {layer.label}
                  </div>
                  <div className="text-[10px] text-muted-foreground truncate">
                    {layer.description}
                  </div>
                </div>

                {/* Toggle icon */}
                {isOpen ? (
                  <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                )}
              </button>

              {/* Layer content */}
              {isOpen && (
                <div className="px-4 pb-3 pt-1">
                  <div className="ml-10 rounded-lg border border-border bg-muted/30 p-3">
                    <pre className="text-[11px] text-foreground leading-relaxed whitespace-pre-wrap font-mono">
                      {layer.content}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
