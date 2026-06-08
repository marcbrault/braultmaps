# Brault Maps

Recursos cartogràfics interactius per a la didàctica cartogràfica i els Sistemes d'Informació Geogràfica (SIG).

## Estructura

```
braultmaps/
├── index.html          → Pàgina d'inici
├── mapes.html          → Llista de mapes
├── projectes.html      → Repositori de projectes
├── recursos.html       → Eines i dades obertes
├── sobre.html          → Sobre el projecte
├── css/
│   └── style.css       → Estils globals
└── mapes/
    ├── gini.html                       → Pàgina del mapa de Gini
    └── BraultMaps_Index_de_Gini.html  → Mapa interactiu de Gini
```

## Com afegir un nou mapa

1. Crea el fitxer HTML del mapa a la carpeta `mapes/`
2. Crea una pàgina de presentació a `mapes/nom-del-mapa.html` (copia l'estructura de `gini.html`)
3. Afegeix l'entrada a `mapes.html`

## Com afegir un nou projecte

Afegeix un bloc `.proj-card` a `projectes.html` amb:
- `data-type`: `mapa`, `analisi` o `visualitzacio`
- Miniatura SVG o imatge
- Títol, descripció i any

## Publicació (GitHub Pages)

Aquest projecte es publica via GitHub Pages des de la branca `main`.

---

© Brault Maps · Cartografia · SIG · Didàctica
