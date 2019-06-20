import sqlite3
from urllib import request
import requests
import progressbar
import os.path as osp

from crawl_videos import create_client


def main():
    browser = create_client()

    conn = sqlite3.connect('links.db')
    conn.row_factory = sqlite3.Row
    videos_info = conn.execute(f'select * from videos where downloaded = 0').fetchall()
    widgets = [progressbar.Percentage(), ' ', progressbar.Counter(), ' ', progressbar.Bar(), ' ',
               progressbar.FileTransferSpeed()]
    pbar = progressbar.ProgressBar(widgets=widgets, max_value=len(videos_info)).start()

    for i, video_info in enumerate(videos_info):
        pbar.update(i)
        video_info = dict(video_info)
        video_id = video_info['video_id']
        browser.visit(video_info['video_url'])
        # if browser.find_by_text('human'):
        video_title = browser.find_by_css('#videoTitle').text
        file_name = f'videos/{video_id}-{video_title}.mp4'
        if osp.exists(file_name):
            with conn:
                conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = "{video_id}"')
            continue
        sizes = [720, 480]
        download_link = None

        download_tab_button = browser.find_by_css('.tab-menu-wrapper-row > .tab-menu-wrapper-cell > .tab-menu-item[data-tab="download-tab"]')
        download_tab_button.click()
        download_tab_button.click()

        download_blocked_div = '.video-actions-tabs > .video-action-tab.download-tab > .verifyEmailWrapper'
        download_blocked_message = 'The download feature of this video has been disabled by'
        if len(browser.find_by_css(download_blocked_div)) > 0 and download_blocked_message in browser.find_by_css(
                download_blocked_div).text:
            print('video download is forbidden')
            continue
        for size in sizes:
            if list(browser.find_link_by_text(f' {size}p')) == 0:
                # size not existing, trying another
                continue
            download_link = browser.find_link_by_text(f' {size}p').first['href']
            break
        if download_link is None:
            raise RuntimeError('link for corresponding size not found')
        # must have here headers, otherwise it behaves as api and does not serve the video
        request.urlretrieve(download_link, file_name)
        print(file_name, 'downloaded')
        with conn:
            conn.execute(f'UPDATE videos SET downloaded = 1 where video_id = "{video_id}"')

    pbar.finish()
    print('done')


if __name__ == '__main__':
    main()
