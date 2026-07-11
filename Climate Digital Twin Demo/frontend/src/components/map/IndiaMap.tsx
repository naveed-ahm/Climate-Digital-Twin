// frontend/src/components/map/IndiaMap.tsx

import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useTwinStore } from '../../store/twinStore';
import { useAlertStore } from '../../store/alertStore';


// SVG Icons for Map Markers
const createSvgIcon = (color: string, iconHtml: string) => {
  return L.divIcon({
    html: `
      <div class="flex items-center justify-center w-8 h-8 rounded-full border border-white/20 shadow-lg backdrop-blur-sm" style="background: ${color}">
        ${iconHtml}
      </div>
    `,
    className: 'custom-leaflet-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
};

const cityIcon = createSvgIcon('rgba(41, 121, 255, 0.7)', '<div class="w-2.5 h-2.5 rounded-full bg-white"></div>');
const activeAlertIcon = createSvgIcon('rgba(255, 61, 87, 0.8)', '<span class="relative flex h-3 w-3"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-white"></span></span>');
const predictedAlertIcon = createSvgIcon('rgba(255, 179, 0, 0.8)', '<span class="text-white text-xs">★</span>');

// Custom Leaflet component to draw the Canvas Heatmap Overlay
const HeatmapOverlay: React.FC = () => {
  const map = useMap();
  const layers = useTwinStore((state) => state.layers);
  const selectedLayer = useTwinStore((state) => state.selectedLayer);

  useEffect(() => {
    if (!layers || !layers[selectedLayer]) return;

    const grid = layers[selectedLayer];
    const canvas = document.createElement('canvas');
    canvas.width = 500;
    canvas.height = 500;

    const bounds = L.latLngBounds([8.0, 68.0], [36.0, 98.0]);
    const imageOverlay = L.imageOverlay(canvas.toDataURL(), bounds, {
      opacity: 0.55,
      interactive: false,
    });

    imageOverlay.addTo(map);

    // Redraw function on canvas
    const drawGrid = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const rows = grid.length;
      const cols = grid[0].length;
      const cellW = canvas.width / cols;
      const cellH = canvas.height / rows;

      // Color maps
      const getColor = (val: number) => {
        if (selectedLayer === 'rainfall') {
          // Blue gradient
          const alpha = Math.min(val / 35.0, 1.0);
          return `rgba(0, 229, 255, ${alpha * 0.75})`;
        } else if (selectedLayer === 'temperature') {
          // Hot/cold gradient
          const alpha = Math.min(Math.max((val - 15.0) / 30.0, 0.0), 1.0);
          return `rgba(255, 61, 87, ${alpha * 0.75})`;
        } else if (selectedLayer === 'soil_moisture') {
          // Green gradient
          return `rgba(0, 230, 118, ${val * 0.75})`;
        } else if (selectedLayer === 'cloud') {
          // White/gray gradient
          return `rgba(255, 255, 255, ${val * 0.7})`;
        } else if (selectedLayer === 'wind') {
          // Blue-purple
          const alpha = Math.min(val / 100.0, 1.0);
          return `rgba(41, 121, 255, ${alpha * 0.75})`;
        } else {
          // Default cyan
          return `rgba(0, 229, 255, ${val * 0.5})`;
        }
      };

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const val = grid[r][c];
          ctx.fillStyle = getColor(val);
          // Draw rect
          ctx.fillRect(c * cellW, r * cellH, cellW + 0.5, cellH + 0.5);
        }
      }

      imageOverlay.setUrl(canvas.toDataURL());
    };

    drawGrid();

    return () => {
      imageOverlay.remove();
    };
  }, [layers, selectedLayer, map]);

  return null;
};

// Component to place markers dynamically on the map
const MapMarkers: React.FC = () => {
  const map = useMap();
  const activeAlerts = useAlertStore((state) => state.activeAlerts);
  const predictions = useAlertStore((state) => state.predictions);
  const selectedAlert = useAlertStore((state) => state.selectedAlert);
  const setSelectedAlert = useAlertStore((state) => state.setSelectedAlert);

  // Focus map on selected alert if it changes
  useEffect(() => {
    if (selectedAlert) {
      map.setView([selectedAlert.location.lat, selectedAlert.location.lon], 6);
    }
  }, [selectedAlert, map]);

  // Layer list of cities in India
  const CITIES = [
    { name: 'Delhi', coords: [28.6, 77.2] },
    { name: 'Mumbai', coords: [19.0, 72.8] },
    { name: 'Chennai', coords: [13.0, 80.2] },
    { name: 'Kolkata', coords: [22.5, 88.3] },
    { name: 'Rajasthan (Desert)', coords: [26.0, 72.0] },
    { name: 'Odisha Coast', coords: [20.2, 86.0] },
    { name: 'Western Ghats', coords: [10.0, 76.5] },
    { name: 'Assam Valley', coords: [26.5, 92.5] },
  ];

  const markerLayerRef = React.useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    // Re-create markers on active alerts & cities
    if (!markerLayerRef.current) {
      markerLayerRef.current = L.layerGroup().addTo(map);
    }
    
    const layerGroup = markerLayerRef.current;
    layerGroup.clearLayers();

    // 1. Draw cities
    CITIES.forEach((city) => {
      L.marker([city.coords[0], city.coords[1]], { icon: cityIcon })
        .bindTooltip(city.name, { permanent: false, direction: 'top' })
        .addTo(layerGroup);
    });

    // 2. Draw active alerts
    activeAlerts.forEach((alert) => {
      const isSelected = selectedAlert?.id === alert.id;
      const marker = L.marker([alert.location.lat, alert.location.lon], { 
        icon: activeAlertIcon 
      })
        .bindTooltip(`🚨 ACTIVE: ${alert.type.toUpperCase()} (${alert.severity.toUpperCase()})`, {
          permanent: isSelected,
          direction: 'top',
          className: 'bg-redAccent border-none text-white font-bold px-2 py-1 rounded text-xs shadow-lg'
        })
        .addTo(layerGroup);

      marker.on('click', () => {
        setSelectedAlert(alert);
      });
    });

    // 3. Draw predicted alerts
    predictions.forEach((pred) => {
      const isSelected = selectedAlert?.id === pred.id;
      const marker = L.marker([pred.location.lat, pred.location.lon], { 
        icon: predictedAlertIcon 
      })
        .bindTooltip(`🔮 FORECAST: ${pred.type.toUpperCase()} (${pred.time_window})`, {
          permanent: isSelected,
          direction: 'top',
          className: 'bg-amberAccent border-none text-void font-bold px-2 py-1 rounded text-xs shadow-lg'
        })
        .addTo(layerGroup);

      marker.on('click', () => {
        setSelectedAlert(pred);
      });
    });

  }, [activeAlerts, predictions, selectedAlert, map]);

  return null;
};

export const IndiaMap: React.FC = () => {
  return (
    <div className="w-full h-full min-h-[450px] relative rounded-xl overflow-hidden border border-white/10 shadow-inner">
      <MapContainer 
        center={[21.0, 78.0]} 
        zoom={5} 
        scrollWheelZoom={true}
        className="w-full h-full z-0 bg-void"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {/* Canvas heatmap layer */}
        <HeatmapOverlay />

        {/* Cities and active disaster marks */}
        <MapMarkers />
      </MapContainer>
    </div>
  );
};
