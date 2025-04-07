import Mp4ClipsExtractor
import SetClipCsvKeywords
import ParseClipsToCsv
import CreateNarration
import TranscriptSeperator
import WorldWar2VideoTranscriptGenerator
import ParseTranscriptsToCsv
import MatchAudioToTranscriptInCsv
import SetTranscriptCsvKeywords
import SetTranscriptCsvLength
import GenerateScenes
import Combine


def main():
    Mp4ClipsExtractor().main()
    ParseClipsToCsv().main()
    SetClipCsvKeywords().main()

    WorldWar2VideoTranscriptGenerator().main()
    TranscriptSeperator().main()
    CreateNarration().main()

    ParseTranscriptsToCsv().main()
    MatchAudioToTranscriptInCsv().main()
    SetTranscriptCsvKeywords().main()
    SetTranscriptCsvLength().main()

    GenerateScenes().main()
    Combine().main()


if __name__ == "__main__":
    main()

