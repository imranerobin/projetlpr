from PIL import Image

def apply_green_filter(image_path, output_path):
    # Charger l'image
    image = Image.open(image_path).convert("RGBA")

    # Modifier les pixels
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]  # Extraire les composantes de couleur

            # Appliquer un filtre vert : on garde la composante verte
            # Et on remplace rouge et bleu par des valeurs pour renforcer l'effet vert
            new_r = int(r * 0.3)  # Réduire l'intensité du rouge
            new_g = g  # Conserver la composante verte
            new_b = int(b * 0.3)  # Réduire l'intensité du bleu

            # Appliquer la nouvelle couleur avec la transparence intacte
            pixels[x, y] = (new_r, new_g, new_b, a)

    # Sauvegarder l'image modifiée
    image.save(output_path)
    image.show()  # Ouvrir l'image modifiée

# Appliquer le filtre vert
apply_green_filter("prise2.png", "prise2vert.png")
