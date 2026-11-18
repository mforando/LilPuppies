"""Candidate breeds for each glyph, as Dog CEO API paths ("breed" or "breed/sub").

Each letter prefers breeds whose name starts with that letter (uppercase and lowercase get
different breeds), so the font is easy to remember: type "B" for a basset hound. Dog CEO has
no breeds starting with Q, U or Z (and only one each for O, V, X and Y), so those glyphs draw
on breeds left over from other letters. The final pick for each glyph is in glyphs.json.
"""

# Display name for each Dog CEO path.
NAMES = {
    "hound/afghan": "Afghan Hound", "akita": "Akita", "airedale": "Airedale Terrier",
    "australian/shepherd": "Australian Shepherd", "cattledog/australian": "Australian Cattle Dog",
    "appenzeller": "Appenzeller",
    "hound/basset": "Basset Hound", "boxer": "Boxer", "beagle": "Beagle", "borzoi": "Borzoi",
    "collie/border": "Border Collie", "mountain/bernese": "Bernese Mountain Dog", "mastiff/bull": "Bullmastiff",
    "terrier/boston": "Boston Terrier", "hound/blood": "Bloodhound", "basenji": "Basenji",
    "chihuahua": "Chihuahua", "spaniel/cocker": "Cocker Spaniel", "chow": "Chow Chow", "rough/collie": "Rough Collie",
    "corgi/cardigan": "Cardigan Welsh Corgi", "terrier/cairn": "Cairn Terrier", "retriever/chesapeake": "Chesapeake Bay Retriever",
    "dachshund": "Dachshund", "dalmatian": "Dalmatian", "doberman": "Doberman Pinscher", "terrier/dandie": "Dandie Dinmont Terrier",
    "setter/english": "English Setter", "springer/english": "English Springer Spaniel", "bulldog/english": "English Bulldog",
    "mastiff/english": "English Mastiff", "entlebucher": "Entlebucher", "eskimo": "American Eskimo Dog",
    "bulldog/french": "French Bulldog", "terrier/fox": "Fox Terrier", "retriever/flatcoated": "Flat-coated Retriever",
    "dane/great": "Great Dane", "german/shepherd": "German Shepherd", "retriever/golden": "Golden Retriever",
    "pointer/german": "German Shorthaired Pointer", "schnauzer/giant": "Giant Schnauzer", "setter/gordon": "Gordon Setter",
    "husky": "Siberian Husky", "havanese": "Havanese",
    "wolfhound/irish": "Irish Wolfhound", "greyhound/italian": "Italian Greyhound", "hound/ibizan": "Ibizan Hound",
    "setter/irish": "Irish Setter", "terrier/irish": "Irish Terrier",
    "spitz/japanese": "Japanese Spitz", "spaniel/japanese": "Japanese Chin",
    "kelpie": "Kelpie", "komondor": "Komondor", "keeshond": "Keeshond", "kuvasz": "Kuvasz", "terrier/kerryblue": "Kerry Blue Terrier",
    "labrador": "Labrador Retriever", "lhasa": "Lhasa Apso", "leonberg": "Leonberger", "terrier/lakeland": "Lakeland Terrier",
    "malamute": "Alaskan Malamute", "pinscher/miniature": "Miniature Pinscher", "maltese": "Maltese", "malinois": "Belgian Malinois",
    "mexicanhairless": "Xoloitzcuintli", "schnauzer/miniature": "Miniature Schnauzer",
    "newfoundland": "Newfoundland", "terrier/norwich": "Norwich Terrier", "elkhound/norwegian": "Norwegian Elkhound",
    "terrier/norfolk": "Norfolk Terrier",
    "otterhound": "Otterhound", "sheepdog/english": "Old English Sheepdog",
    "pug": "Pug", "poodle/standard": "Standard Poodle", "pomeranian": "Pomeranian", "papillon": "Papillon",
    "pembroke": "Pembroke Welsh Corgi", "pekinese": "Pekingese", "pyrenees": "Great Pyrenees", "hound/plott": "Plott Hound",
    "rottweiler": "Rottweiler", "ridgeback/rhodesian": "Rhodesian Ridgeback", "redbone": "Redbone Coonhound",
    "terrier/russell": "Russell Terrier",
    "saluki": "Saluki", "stbernard": "St. Bernard", "samoyed": "Samoyed", "shiba": "Shiba Inu",
    "terrier/scottish": "Scottish Terrier", "sheepdog/shetland": "Shetland Sheepdog", "sharpei": "Shar-Pei",
    "bullterrier/staffordshire": "Staffordshire Bull Terrier", "deerhound/scottish": "Scottish Deerhound",
    "mastiff/tibetan": "Tibetan Mastiff", "terrier/toy": "Toy Terrier", "tervuren": "Belgian Tervuren",
    "terrier/tibetan": "Tibetan Terrier", "poodle/toy": "Toy Poodle",
    "vizsla": "Vizsla",
    "weimaraner": "Weimaraner", "whippet": "Whippet", "terrier/westhighland": "West Highland White Terrier",
    "terrier/welsh": "Welsh Terrier", "terrier/wheaten": "Soft-coated Wheaten Terrier",
    "terrier/yorkshire": "Yorkshire Terrier",
}

ALL = sorted(NAMES)
