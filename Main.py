import Mp4ClipsExtractor
import SetClipCsvKeywords
import ParseClipsToCsv
import CreateNarration
import TranscriptSeperator
import VideoTranscriptGenerator
import ParseTranscriptsToCsv
import MatchAudioToTranscriptInCsv
import SetTranscriptCsvLength
import GenerateScenes
import Combine
import ExpandTranscript
import Research
import TranscriptPurifier
def main():
   # Mp4ClipsExtractor().main()
    #ParseClipsToCsv().main()
   # SetClipCsvKeywords().main()

    #Research().main()
    #VideoTranscriptGenerator().main()
    #ExpandTranscript().main()
    #TranscriptPurifier().main()
    #TranscriptSeperator().main()
    #CreateNarration().main()

    ParseTranscriptsToCsv().main()
    MatchAudioToTranscriptInCsv().main()
    SetTranscriptCsvLength().main()

    GenerateScenes().main()
    #Combine().main()


if __name__ == "__main__":
    main()

