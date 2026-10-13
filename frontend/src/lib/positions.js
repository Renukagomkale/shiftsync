const known = {
  Barista: "bg-tangerine",
  Cashier: "bg-mint",
  Baker: "bg-butter",
  Floor: "bg-rose",
};

const fallback = ["bg-tangerine", "bg-mint", "bg-butter", "bg-rose"];

export const positionNames = Object.keys(known);

export function positionColor(name) {
  if (known[name]) return known[name];
  const sum = [...name].reduce((total, char) => total + char.charCodeAt(0), 0);
  return fallback[sum % fallback.length];
}
