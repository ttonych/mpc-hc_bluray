// Inspect an actual HEVC access unit with and without the probe-only option.
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>

static uint64_t hash_bytes(const uint8_t *data, size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t i = 0; i < size; ++i)
        hash = (hash ^ data[i]) * UINT64_C(1099511628211);
    return hash;
}

static int inspect(const AVPacket *packet, int enable)
{
    const AVCodec *codec = avcodec_find_decoder_by_name("hevc");
    AVCodecContext *ctx = avcodec_alloc_context3(codec);
    AVFrame *frame = av_frame_alloc();
    if (!codec || !ctx || !frame) return 1;
    ctx->thread_count = 1;
    if (enable && av_opt_set_int(ctx->priv_data, "probe_idr_headers", 1, 0) < 0) return 2;
    if (avcodec_open2(ctx, codec, NULL) < 0 || avcodec_send_packet(ctx, packet) < 0) return 3;

    unsigned frames = 0;
    for (int drain = 0; drain <= 1; ++drain) {
        if (drain && avcodec_send_packet(ctx, NULL) < 0) return 4;
        int ret;
        while ((ret = avcodec_receive_frame(ctx, frame)) >= 0) {
            int bytes = av_image_get_buffer_size(frame->format, frame->width, frame->height, 1);
            if (bytes <= 0) return 5;
            uint8_t *pixels = av_malloc(bytes);
            if (!pixels || av_image_copy_to_buffer(pixels, bytes, (const uint8_t *const *)frame->data,
                              frame->linesize, frame->format, frame->width, frame->height, 1) != bytes)
                return 6;
            printf("frame %d %d %"PRIx64"\n", frame->width, frame->height, hash_bytes(pixels, bytes));
            av_free(pixels);
            for (int i = 0; i < frame->nb_side_data; ++i) {
                const AVFrameSideData *sd = frame->side_data[i];
                size_t size = sd->size;
                if (sd->type == AV_FRAME_DATA_S12M_TIMECODE) {
                    // The first word gives the number of meaningful timecodes.
                    if (size != 4 * sizeof(uint32_t)) return 9;
                    uint32_t count = *(const uint32_t *)sd->data;
                    if (count > 3) return 9;
                    size = (count + 1) * sizeof(uint32_t);
                }
                printf("side %s %"PRIx64"\n", av_frame_side_data_name(sd->type), hash_bytes(sd->data, size));
            }
            ++frames;
            av_frame_unref(frame);
        }
        if (ret != AVERROR(EAGAIN) && ret != AVERROR_EOF) return 7;
    }
    printf("parameters %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d/%d %d/%d %d\n",
           ctx->width, ctx->height, ctx->coded_width, ctx->coded_height, ctx->pix_fmt,
           ctx->profile, ctx->level, ctx->has_b_frames, ctx->color_range, ctx->color_primaries,
           ctx->color_trc, ctx->colorspace, ctx->chroma_sample_location, ctx->field_order,
           ctx->sample_aspect_ratio.num, ctx->sample_aspect_ratio.den,
           ctx->framerate.num, ctx->framerate.den, ctx->bits_per_raw_sample);
    printf("frames %u\n", frames);
    av_frame_free(&frame);
    avcodec_free_context(&ctx);
    return 0;
}

int main(int argc, char **argv)
{
    AVFormatContext *format = NULL;
    AVPacket *packet = av_packet_alloc();
    if (argc != 3 || !packet || avformat_open_input(&format, argv[1], av_find_input_format("hevc"), NULL) < 0 ||
        av_read_frame(format, packet) < 0)
        return 8;
    int ret = inspect(packet, atoi(argv[2]));
    if (!ret) {
        puts("playback");
        ret = inspect(packet, 0);
    }
    av_packet_free(&packet);
    avformat_close_input(&format);
    return ret;
}
