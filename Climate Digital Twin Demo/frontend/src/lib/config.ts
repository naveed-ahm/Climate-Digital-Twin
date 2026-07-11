// frontend/src/lib/config.ts

export const GRID_SIZE = 15;

export const REGIONS: Record<string, [number, number]> = {
  "Delhi": [28.6, 77.2],
  "Mumbai": [19.0, 72.8],
  "Chennai": [13.0, 80.2],
  "Kolkata": [22.5, 88.3],
  "Rajasthan (Desert)": [26.0, 72.0],
  "Sundarbans (Delta)": [21.9, 88.8],
  "Odisha Coast": [20.2, 86.0],
  "Western Ghats": [10.0, 76.5],
  "Assam Valley": [26.5, 92.5]
};

export const LAT_MIN = 8.0;
export const LAT_MAX = 36.0;
export const LON_MIN = 68.0;
export const LON_MAX = 98.0;

export function get_grid_coords() {
  const lats: number[] = [];
  const lons: number[] = [];
  
  // Linspace logic in JS
  for (let i = 0; i < GRID_SIZE; i++) {
    lats.push(LAT_MAX - (i * (LAT_MAX - LAT_MIN)) / (GRID_SIZE - 1));
    lons.push(LON_MIN + (i * (LON_MAX - LON_MIN)) / (GRID_SIZE - 1));
  }
  return { lats, lons };
}
