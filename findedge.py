from PIL import Image, ImageFilter

img = Image.open("clue.png").convert("L")
edges = img.filter(ImageFilter.FIND_EDGES)
edges.save("edges_pillow.png")
