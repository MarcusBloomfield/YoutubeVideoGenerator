import Mp4ClipsExtractor
import SetClipCsvKeywords
import ParseClipsToCsv
import CreateNarration
import TranscriptSeperator
import WorldWar2VideoTranscriptGenerator
import ParseTranscriptsToCsv
import MatchAudioToTranscriptInCsv
import SetTranscriptCsvLength
import GenerateScenes
import Combine
import ExpandTranscript
import Research

def main():
    Mp4ClipsExtractor().main()
    ParseClipsToCsv().main()
    SetClipCsvKeywords().main()

    Research().main()
    WorldWar2VideoTranscriptGenerator().main()
    ExpandTranscript().main()
    TranscriptSeperator().main()
    CreateNarration().main()

    ParseTranscriptsToCsv().main()
    MatchAudioToTranscriptInCsv().main()
    SetTranscriptCsvLength().main()

    GenerateScenes().main()
    Combine().main()


if __name__ == "__main__":
    main()

