"""
多线程新闻爬虫系统 - 完整实现
功能：爬取、存储、搜索、分析新闻数据
仅作为Python项目智能包管理工具的示例问题，不直接属于项目
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import queue
import time
import hashlib
import re
from collections import Counter
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba
import os

class NewsDatabase:
    """数据库管理类"""
    
    def __init__(self, db_name='news.db'):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                content TEXT,
                author TEXT,
                publish_time TEXT,
                comments_count INTEGER DEFAULT 0,
                url_hash TEXT UNIQUE NOT NULL,
                crawl_time TEXT NOT NULL,
                source TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_url_hash ON news(url_hash)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_title ON news(title)
        ''')
        
        conn.commit()
        conn.close()
    
    def url_exists(self, url):
        """检查URL是否已存在"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM news WHERE url_hash = ?', (url_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def insert_news(self, news_item):
        """插入新闻数据"""
        url_hash = hashlib.md5(news_item['url'].encode()).hexdigest()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO news (title, url, content, author, publish_time, 
                                comments_count, url_hash, crawl_time, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_item.get('title', ''),
                news_item.get('url', ''),
                news_item.get('content', ''),
                news_item.get('author', ''),
                news_item.get('publish_time', ''),
                news_item.get('comments_count', 0),
                url_hash,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                news_item.get('source', '')
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def search_news(self, keyword, limit=10):
        """搜索新闻"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, url, content, publish_time, comments_count 
            FROM news 
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY comments_count DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_news(self):
        """获取所有新闻"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT title, content, publish_time, comments_count FROM news')
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_stats(self):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM news')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT AVG(comments_count) FROM news')
        avg_comments = cursor.fetchone()[0] or 0
        conn.close()
        return {'total': total, 'avg_comments': avg_comments}


class NewsCrawler:
    """新闻爬虫类"""
    
    def __init__(self, db, num_threads=5):
        self.db = db
        self.url_queue = queue.Queue()
        self.num_threads = num_threads
        self.crawled_count = 0
        self.lock = threading.Lock()
        self.stop_flag = False
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def add_url(self, url, source=''):
        """添加URL到队列"""
        if not self.db.url_exists(url):
            self.url_queue.put({'url': url, 'source': source})
    
    def parse_hackernews(self, html, base_url):
        """解析Hacker News页面"""
        soup = BeautifulSoup(html, 'html.parser')
        news_items = []
        
        # 查找所有新闻条目
        rows = soup.find_all('tr', class_='athing')
        
        for row in rows:
            try:
                # 获取标题和链接
                title_elem = row.find('span', class_='titleline')
                if not title_elem:
                    continue
                
                link = title_elem.find('a')
                if not link:
                    continue
                
                title = link.text.strip()
                url = link.get('href', '')
                
                # 处理相对URL
                if url.startswith('item?id='):
                    url = urljoin(base_url, url)
                
                # 获取评论数等信息
                subtext_row = row.find_next_sibling('tr')
                comments_count = 0
                author = ''
                
                if subtext_row:
                    subtext = subtext_row.find('td', class_='subtext')
                    if subtext:
                        # 获取作者
                        author_elem = subtext.find('a', class_='hnuser')
                        if author_elem:
                            author = author_elem.text.strip()
                        
                        # 获取评论数
                        comments_elem = subtext.find_all('a')
                        for elem in comments_elem:
                            text = elem.text
                            if 'comment' in text:
                                match = re.search(r'(\d+)', text)
                                if match:
                                    comments_count = int(match.group(1))
                
                news_items.append({
                    'title': title,
                    'url': url,
                    'author': author,
                    'comments_count': comments_count,
                    'content': title,  # HN只有标题
                    'publish_time': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'HackerNews'
                })
                
            except Exception as e:
                print(f"解析条目出错: {e}")
                continue
        
        return news_items
    
    def fetch_and_parse(self, url, source):
        """抓取并解析页面"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # 根据来源选择解析方法
            if 'news.ycombinator.com' in url:
                return self.parse_hackernews(response.text, url)
            else:
                # 通用解析（简化版）
                soup = BeautifulSoup(response.text, 'html.parser')
                return [{
                    'title': soup.title.string if soup.title else 'No Title',
                    'url': url,
                    'content': soup.get_text()[:500],
                    'source': source,
                    'publish_time': datetime.now().strftime('%Y-%m-%d'),
                    'comments_count': 0
                }]
        
        except Exception as e:
            print(f"抓取 {url} 失败: {e}")
            return []
    
    def worker(self):
        """工作线程"""
        while not self.stop_flag:
            try:
                item = self.url_queue.get(timeout=1)
                url = item['url']
                source = item['source']
                
                print(f"[线程 {threading.current_thread().name}] 正在抓取: {url}")
                
                news_items = self.fetch_and_parse(url, source)
                
                for news_item in news_items:
                    if self.db.insert_news(news_item):
                        with self.lock:
                            self.crawled_count += 1
                        print(f"✓ 保存: {news_item['title'][:50]}")
                
                self.url_queue.task_done()
                time.sleep(1)  # 礼貌性延迟
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"工作线程错误: {e}")
    
    def start(self):
        """启动爬虫"""
        threads = []
        for i in range(self.num_threads):
            t = threading.Thread(target=self.worker, name=f"Worker-{i+1}")
            t.daemon = True
            t.start()
            threads.append(t)
        
        print(f"已启动 {self.num_threads} 个工作线程")
        return threads
    
    def wait_completion(self):
        """等待所有任务完成"""
        self.url_queue.join()
        self.stop_flag = True
        print(f"\n爬取完成！共保存 {self.crawled_count} 条新闻")


class NewsAnalyzer:
    """新闻分析类"""
    
    def __init__(self, db):
        self.db = db
    
    def generate_wordcloud(self, output_file='wordcloud.png'):
        """生成词云"""
        news_list = self.db.get_all_news()
        
        # 合并所有文本
        text = ' '.join([item[0] + ' ' + (item[1] or '') for item in news_list])
        
        # 中文分词
        words = jieba.cut(text)
        text_cut = ' '.join(words)
        
        # 生成词云
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path='simhei.ttf' if os.path.exists('simhei.ttf') else None,
            max_words=100
        ).generate(text_cut)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('新闻热词词云', fontsize=16)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        print(f"词云已保存到: {output_file}")
    
    def analyze_hot_topics(self, top_n=10):
        """分析热门话题"""
        news_list = self.db.get_all_news()
        
        # 提取所有标题的关键词
        all_words = []
        for item in news_list:
            title = item[0]
            words = jieba.cut(title)
            all_words.extend([w for w in words if len(w) > 1])
        
        # 统计词频
        word_freq = Counter(all_words)
        hot_topics = word_freq.most_common(top_n)
        
        print(f"\n{'='*50}")
        print(f"热门话题 TOP {top_n}")
        print(f"{'='*50}")
        for i, (word, count) in enumerate(hot_topics, 1):
            print(f"{i}. {word}: {count} 次")
        
        return hot_topics
    
    def analyze_time_distribution(self, output_file='time_dist.png'):
        """分析时间分布"""
        news_list = self.db.get_all_news()
        
        # 统计发布日期
        dates = [item[2] for item in news_list if item[2]]
        date_counter = Counter(dates)
        
        if not date_counter:
            print("没有足够的时间数据")
            return
        
        # 绘图
        dates_sorted = sorted(date_counter.items())
        x = [d[0] for d in dates_sorted]
        y = [d[1] for d in dates_sorted]
        
        plt.figure(figsize=(12, 6))
        plt.bar(x, y, color='steelblue')
        plt.xlabel('日期', fontsize=12)
        plt.ylabel('新闻数量', fontsize=12)
        plt.title('新闻发布时间分布', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        print(f"时间分布图已保存到: {output_file}")
    
    def generate_report(self):
        """生成分析报告"""
        stats = self.db.get_stats()
        
        report = f"""
{'='*60}
新闻数据分析报告
{'='*60}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

统计信息:
  - 新闻总数: {stats['total']} 条
  - 平均评论数: {stats['avg_comments']:.2f}

热门话题分析:
"""
        print(report)
        
        # 分析热门话题
        self.analyze_hot_topics(10)
        
        # 生成可视化
        try:
            self.generate_wordcloud()
            self.analyze_time_distribution()
            print("\n可视化图表已生成！")
        except Exception as e:
            print(f"生成可视化时出错: {e}")


def main():
    """主函数"""
    print("="*60)
    print("多线程新闻爬虫系统")
    print("="*60)
    
    # 初始化数据库
    db = NewsDatabase()
    
    # 创建爬虫
    crawler = NewsCrawler(db, num_threads=3)
    
    # 添加要爬取的URL
    urls = [
        ('https://news.ycombinator.com/', 'HackerNews'),
        ('https://news.ycombinator.com/newest', 'HackerNews'),
    ]
    
    for url, source in urls:
        crawler.add_url(url, source)
    
    # 启动爬虫
    print("\n开始爬取...")
    threads = crawler.start()
    
    # 等待完成
    crawler.wait_completion()
    
    # 等待所有线程结束
    for t in threads:
        t.join(timeout=2)
    
    # 搜索演示
    print("\n" + "="*60)
    print("搜索功能演示")
    print("="*60)
    keyword = "AI"
    results = db.search_news(keyword, limit=5)
    print(f"\n搜索关键词: {keyword}")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result[0]}")
        print(f"   URL: {result[1]}")
        print(f"   评论数: {result[4]}")
    
    # 数据分析
    print("\n" + "="*60)
    print("数据分析")
    print("="*60)
    analyzer = NewsAnalyzer(db)
    analyzer.generate_report()
    
    print("\n✓ 所有任务完成！")
    print(f"数据库文件: {db.db_name}")


if __name__ == '__main__':
    main()