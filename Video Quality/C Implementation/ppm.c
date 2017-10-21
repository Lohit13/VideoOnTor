#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libswscale/swscale.h>

void SaveFrame(AVFrame *pFrame, int width, int height, int iFrame, int type) {
  FILE *pFile;
  char szFilename[32];
  int  y;
  
  // Open file
  if(type == 0){
  	sprintf(szFilename, "ref_ppm/frame%d.ppm", iFrame);
  }
  if(type == 1){
  	sprintf(szFilename, "check_ppm/frame%d.ppm", iFrame);
  }

  pFile=fopen(szFilename, "wb");
  if(pFile==NULL)
    return;
  
  // Write header
  fprintf(pFile, "P6\n%d %d\n255\n", width, height);
  
  // Write pixel data
  for(y=0; y<height; y++)
    fwrite(pFrame->data[0]+y*pFrame->linesize[0], 1, width*3, pFile);
  
  // Close file
  fclose(pFile);
}

// type - 0 ref, 1 check
void save_ppm(char *video, int type){
	AVFormatContext *pFormatCtx = NULL;

	// Open video file
	if(avformat_open_input(&pFormatCtx, video, NULL, NULL)!=0)
	  return -1; // Couldn't open file

	// Retrieve stream information
	if(avformat_find_stream_info(pFormatCtx, NULL)<0)
  		return -1; // Couldn't find stream information

  	// Dump information about file onto standard error
	//av_dump_format(pFormatCtx, 0, video, 0);

  	int i;
	AVCodecContext *pCodecCtxOrig = NULL;
	AVCodecContext *pCodecCtx = NULL;

	AVCodec *pCodec = NULL;

	// Find the first video stream
	int videoStream=-1;
	for(i=0; i<pFormatCtx->nb_streams; i++)
	  if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_VIDEO) {
	    videoStream=i;
	    break;
	  }
	if(videoStream==-1)
	  return -1; // Didn't find a video stream

	// Get a pointer to the codec context for the video stream
	pCodecCtx=pFormatCtx->streams[videoStream]->codec;

	pCodec = avcodec_find_decoder(pCodecCtx->codec_id);
    if(pCodec==NULL) return -15; //codec not found
 
    if(avcodec_open2(pCodecCtx,pCodec,NULL) < 0) return -16;
 
    AVFrame *pFrame = NULL;
    AVFrame *pFrameRGB = NULL;
    pFrame    = av_frame_alloc();
    pFrameRGB = av_frame_alloc();


    uint8_t *buffer;
    int numBytes;
 
    numBytes = avpicture_get_size(AV_PIX_FMT_BGR24,pCodecCtx->width,pCodecCtx->height) ; //AV_PIX_FMT_RGB24
    buffer = (uint8_t *) av_malloc(numBytes*sizeof(uint8_t));
    avpicture_fill((AVPicture *) pFrameRGB,buffer,AV_PIX_FMT_BGR24,pCodecCtx->width,pCodecCtx->height);
 

    int res;
    int frameFinished;
    AVPacket packet;

    // Count number of frames in video
    int numFrames = 0;
    while(res = av_read_frame(pFormatCtx,&packet)>=0)
    {
        if(packet.stream_index == videoStream){
            avcodec_decode_video2(pCodecCtx,pFrame,&frameFinished,&packet);
            if(frameFinished){

            	printf("%d\n",numFrames);
 				numFrames += 1;
 				SaveFrame(pFrameRGB, pCodecCtx->width, pCodecCtx->height, numFrames, type);

                av_free_packet(&packet);
            }
        }
    }    

	// Free the RGB image
	av_free(buffer);
	av_free(pFrameRGB);

	// Free the YUV frame
	av_free(pFrame);

	// Close the codecs
	avcodec_close(pCodecCtx);
	avcodec_close(pCodecCtxOrig);

	// Close the video file
	avformat_close_input(&pFormatCtx);

}

int main(int argc, char *argv[]) {

	if(argc < 3){
		perror("Invalid arguments. Usage: psnr <reference_video> <video>\n");
		return 0;
	}

	char *ref_video = (char *)malloc(strlen(argv[1])*sizeof(char));
	strcpy(ref_video, argv[1]);

	char *check_video = (char *)malloc(strlen(argv[1])*sizeof(char));
	strcpy(check_video, argv[2]);

	av_register_all();

	save_ppm(ref_video, 0);
	save_ppm(check_video, 1);

	return 0;

}