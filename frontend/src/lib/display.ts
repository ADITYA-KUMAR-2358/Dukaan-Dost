export function displayQuantity(value: number | null, unit?: string) {
  if (value === null) return "Not set";
  const formatted = new Intl.NumberFormat("en-IN").format(value);
  return unit ? `${formatted} ${unit}` : formatted;
}
