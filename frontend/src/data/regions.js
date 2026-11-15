export const COUNTRIES = [
  {
    id: 'nigeria',
    name: 'Nigeria',
    code: 'NG',
    regions: [
      { id: 'kano', name: 'Kano', zone: 'Sudan Savanna', lat: 12.0022, lon: 8.5919 },
      { id: 'kaduna', name: 'Kaduna', zone: 'Guinea Savanna', lat: 10.5222, lon: 7.4383 },
      { id: 'jos', name: 'Jos', zone: 'Jos Plateau', lat: 9.8965, lon: 8.8583 },
      { id: 'makurdi', name: 'Makurdi', zone: 'Southern Guinea', lat: 7.7322, lon: 8.5391 },
      { id: 'sokoto', name: 'Sokoto', zone: 'Sahel', lat: 13.0059, lon: 5.2476 },
      { id: 'zaria', name: 'Zaria', zone: 'Sudan Savanna', lat: 11.0855, lon: 7.7199 },
    ],
  },
  {
    id: 'ghana',
    name: 'Ghana',
    code: 'GH',
    regions: [
      { id: 'tamale', name: 'Tamale', zone: 'Northern Savanna', lat: 9.4008, lon: -0.8393 },
      { id: 'kumasi', name: 'Kumasi', zone: 'Forest belt', lat: 6.6885, lon: -1.6244 },
      { id: 'accra', name: 'Accra', zone: 'Coastal', lat: 5.6037, lon: -0.187 },
    ],
  },
  {
    id: 'kenya',
    name: 'Kenya',
    code: 'KE',
    regions: [
      { id: 'nairobi', name: 'Nairobi', zone: 'Central highlands', lat: -1.2921, lon: 36.8219 },
      { id: 'nakuru', name: 'Nakuru', zone: 'Rift Valley', lat: -0.3031, lon: 36.08 },
      { id: 'eldoret', name: 'Eldoret', zone: 'Highlands', lat: 0.5143, lon: 35.2698 },
      { id: 'mombasa', name: 'Mombasa', zone: 'Coastal', lat: -4.0435, lon: 39.6682 },
    ],
  },
  {
    id: 'india',
    name: 'India',
    code: 'IN',
    regions: [
      { id: 'ludhiana', name: 'Ludhiana', zone: 'Punjab', lat: 30.901, lon: 75.8573 },
      { id: 'nagpur', name: 'Nagpur', zone: 'Deccan', lat: 21.1458, lon: 79.0882 },
      { id: 'hyderabad', name: 'Hyderabad', zone: 'Telangana', lat: 17.385, lon: 78.4867 },
    ],
  },
  {
    id: 'brazil',
    name: 'Brazil',
    code: 'BR',
    regions: [
      { id: 'sorriso', name: 'Sorriso', zone: 'Mato Grosso', lat: -12.5453, lon: -55.7113 },
      { id: 'barreiras', name: 'Barreiras', zone: 'Bahia', lat: -12.1528, lon: -44.99 },
      { id: 'cascavel', name: 'Cascavel', zone: 'Paraná', lat: -24.9555, lon: -53.4552 },
    ],
  },
  {
    id: 'usa',
    name: 'United States',
    code: 'US',
    regions: [
      { id: 'iowa', name: 'Iowa', zone: 'Corn Belt', lat: 42.0, lon: -93.5 },
      { id: 'kansas', name: 'Kansas', zone: 'Great Plains', lat: 38.5, lon: -98.0 },
      { id: 'nebraska', name: 'Nebraska', zone: 'High Plains', lat: 41.5, lon: -99.8 },
    ],
  },
]

export const DEFAULT_COUNTRY = 'nigeria'
export const DEFAULT_REGION = 'kano'

export function findCountry(id) {
  return COUNTRIES.find((c) => c.id === id) || COUNTRIES[0]
}

export function findRegion(countryId, regionId) {
  const country = findCountry(countryId)
  return country.regions.find((r) => r.id === regionId) || country.regions[0]
}

export function locationFromRegion(region) {
  return {
    lat: region.lat,
    lon: region.lon,
    label: region.name,
    name: region.name,
    zone: region.zone,
  }
}
