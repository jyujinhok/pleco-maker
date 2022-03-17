# plecomake

This tool uses articledata.json and dial.json (copied in from https://github.com/jyujinhok/wiktionary-zh-extract) to make a Pleco importable csv dictionary.

The dictionary will contain:

 - Dialectical synonym data for all lects in `LECTS`
 - Pronunciation data for all lects in `PRONS`

and will only generate entries for cases where `REQUIRED_PRONS` has a pronunciation or `REQUIRED_LECTS` has a distinct synonym.

CSV dictionaries can be imported by going to "Manage dictionaries" in Pleco's settings, creating a new dictionary (give it a new short code, too, I use WIKT), and importing entries. To import a new set you either have to delete and recreate the dictionary or use "undo last import". Imports are unfortunately very slow, but the Pleco .pdb format is not super documented and not intended to be used for this.

An issue with the current model is that it will not associate entries with existing entries if the headword is not *exactly* right, including both simplified and traditional characters (we only use traditional, though technically we could fetch simplified stuff by parsing the zh-forms templates). However, the creater of Pleco has [suggested](https://plecoforums.com/threads/associating-imported-custom-entries-with-existing-entries-not-working-well.6891/) using the flashcard system instead and then using "convert to custom dict".